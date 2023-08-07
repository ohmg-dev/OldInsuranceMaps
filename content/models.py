'''
This is a step toward moving database models from the loc_insurancemaps app into
this content app. At present, these are not Django models or even Django proxy models,
just light-weight objects that are instantiated through the Volume and related
models. This will allow the codebase to slowly evolve before actually changing any
database content and running migrations.

The eventual migration plan is this:

loc_insurancemaps.models.Volume --> content.models.Item
loc_insurancemaps.models.Sheet  --> content.models.Resource

new model                       --> content.models.ItemConfigPreset
    This would allow an extraction of Sanborn-specific properties vs. generic item
    uploads. Still unclear exactly what to call this, or everything that it would have.
'''

import os
import glob
import json
from datetime import datetime
import logging

from django.conf import settings
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.core.files import File
from osgeo import gdal

from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.backends import MosaicBackend

from georeference.models.resources import Layer
from georeference.utils import random_alnum
from loc_insurancemaps.models import Volume, Sheet

logger = logging.getLogger(__name__)

def write_trim_feature_cache(feature, file_path):
    with open(file_path, "w") as f:
        json.dump(feature, f, indent=2)

def read_trim_feature_cache(file_path):
    with open(file_path, "r") as f:
        feature = json.load(f)
    return feature

class Item:

    def __init__(self, volume_pk):

        self.vol = Volume.objects.get(pk=volume_pk)

    def generate_mosaic_cog(self):
        """ A helpful reference from the BPLv used during the creation of this method:
        https://github.com/bplmaps/atlascope-utilities/blob/master/new-workflow/atlas-tools.py
        """

        start = datetime.now()

        gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
        gdal.SetConfigOption("GDAL_TIFF_INTERNAL_MASK", "YES")

        multimask_geojson = self.vol.get_multimask_geojson()
        multimask_file_name = f"multimask-{self.vol.identifier}"
        multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
        with open(multimask_file, "w") as out:
            json.dump(multimask_geojson, out, indent=1)

        trim_list = []
        layer_extent_polygons = []
        for feature in multimask_geojson['features']:

            layer_name = feature['properties']['layer']

            layer = Layer.objects.get(slug=layer_name)
            if not layer.file:
                raise Exception(f"no layer file for this layer {layer_name}")

            if layer.extent:
                extent_poly = Polygon.from_bbox(layer.extent)
                layer_extent_polygons.append(extent_poly)

            in_path = layer.file.path
            trim_name = os.path.basename(in_path).replace(".tif", "_trim.vrt")
            out_path = os.path.join(settings.TEMP_DIR, trim_name)

            wo = gdal.WarpOptions(
                # format="COG",
                format="VRT",
                dstSRS = "EPSG:3857",
                cutlineDSName = multimask_file,
                cutlineLayer = multimask_file_name,
                cutlineWhere = f"layer='{layer_name}'",
                cropToCutline = True,
                # srcAlpha = True,
                # dstAlpha = True,
                # creationOptions= [
                #     'COMPRESS=JPEG',
                # ]
                # creationOptions= [
                #     'COMPRESS=DEFLATE',
                #     'PREDICTOR=2',
                # ]
            )
            gdal.Warp(out_path, in_path, options=wo)
            print("warped")

            trim_list.append(out_path)

        if len(layer_extent_polygons) > 0:
            multi = MultiPolygon(layer_extent_polygons, srid=4326)

        mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{self.vol.identifier}.vrt")
        bounds = multi.transform(3857, True).extent
        vo = gdal.BuildVRTOptions(
            resolution = 'highest',
            outputSRS="EPSG:3857",
            outputBounds=bounds,
            separate = False,
            # addAlpha = True,
            # srcNodata = "255 255 255",
        )
        print("building vrt")

        mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{self.vol.identifier}.vrt")
        gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)

        print("building final geotiff")

        to = gdal.TranslateOptions(
            format="COG",
            creationOptions = [
                "COMPRESS=JPEG",
            ],
        )

        mosaic_tif = mosaic_vrt.replace(".vrt", ".tif")
        gdal.Translate(mosaic_tif, mosaic_vrt, options=to)

        existing_file_path = None
        if self.vol.mosaic_geotiff:
            existing_file_path = self.vol.mosaic_geotiff.path

        file_name = f"{self.vol.identifier}__{random_alnum(6)}.tif"

        with open(mosaic_tif, 'rb') as f:
            self.vol.mosaic_geotiff.save(file_name, File(f))

        # os.remove(mosaic_tif)
        if existing_file_path:
            os.remove(existing_file_path)

        self.vol.mosaic_preference = "geotiff"
        self.vol.save(update_fields=['mosaic_preference'])

        print(f"completed - elapsed time: {datetime.now() - start}")

    def generate_mosaic_json(self, trim_all=False):

        logger.info(f"{self.vol.identifier} | generating mosaic json")

        multimask_geojson = self.vol.get_multimask_geojson()
        multimask_file_name = f"multimask-{self.vol.identifier}"
        multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
        with open(multimask_file, "w") as out:
            json.dump(multimask_geojson, out, indent=1)

        logger.debug(f"{self.vol.identifier} | multimask loaded")
        logger.info(f"{self.vol.identifier} | iterating and trimming layers")
        trim_list = []
        for feature in multimask_geojson['features']:

            layer_name = feature['properties']['layer']
            layer = Layer.objects.get(slug=layer_name)
            if not layer.file:
                logger.error(f"{self.vol.identifier} | no layer file for this layer {layer_name}")
                raise Exception(f"no layer file for this layer {layer_name}")
            in_path = layer.file.path

            layer_dir = os.path.dirname(in_path)
            file_name = os.path.basename(in_path)
            logger.debug(f"{self.vol.identifier} | processing layer file {file_name}")

            file_root = os.path.splitext(file_name)[0]
            existing_trimmed_tif = glob.glob(f"{layer_dir}/{file_root}*_trim.tif")
            print(existing_trimmed_tif)

            feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
            if os.path.isfile(feat_cache_path):
                cached_feature = read_trim_feature_cache(feat_cache_path)
                logger.debug(f"{self.vol.identifier} | using cached trim json boundary")
            else:
                cached_feature = None
                write_trim_feature_cache(feature, feat_cache_path)

            unique_id = random_alnum(6)
            trim_vrt_path = in_path.replace(".tif", f"_{unique_id}_trim.vrt")
            out_path = trim_vrt_path.replace(".vrt", ".tif")

            # compare this multimask feature to the cached one for this layer
            # and only (re)create a trimmed tif if they do not match
            if feature != cached_feature or trim_all is True:

                wo = gdal.WarpOptions(
                    format="VRT",
                    dstSRS = "EPSG:3857",
                    cutlineDSName = multimask_file,
                    cutlineLayer = multimask_file_name,
                    cutlineWhere = f"layer='{layer_name}'",
                    cropToCutline = True,
                    creationOptions = ['COMPRESS=LZW', 'BIGTIFF=YES'],
                    resampleAlg = 'cubic',
                    dstAlpha = False,
                    dstNodata = "255 255 255",
                )
                gdal.Warp(trim_vrt_path, in_path, options=wo)

                to = gdal.TranslateOptions(
                    format="GTiff",
                    bandList = [1,2,3],
                    creationOptions = [
                        "TILED=YES",
                        "COMPRESS=LZW",
                        "PREDICTOR=2",
                        "NUM_THREADS=ALL_CPUS",
                        ## the following is apparently in the COG spec but doesn't work??
                        # "COPY_SOURCE_OVERVIEWS=YES",
                    ],
                )

                logger.debug(f"writing trimmed tif {os.path.basename(out_path)}")
                result = gdal.Translate(out_path, trim_vrt_path, options=to)
                write_trim_feature_cache(feature, feat_cache_path)

                img = gdal.Open(out_path, 1)
                if img is None:
                    logger.warn(f"{self.vol.identifier} | file was not properly created, omitting: {file_name}")
                    continue   
                logger.debug(f"{self.vol.identifier} | building overview: {file_name}")
                gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
                gdal.SetConfigOption("PREDICTOR", "2")
                gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
                img.BuildOverviews("AVERAGE", [2, 4, 8, 16])

            else:
                logger.debug(f"{self.vol.identifier} | using existing trimmed tif {file_name}")

            trim_list.append(out_path)

        trim_urls = [
            i.replace(os.path.dirname(settings.MEDIA_ROOT), settings.MEDIA_HOST.rstrip("/")) \
                for i in trim_list
        ]
        logger.info(f"{self.vol.identifier} | writing mosaic from {len(trim_urls)} trimmed tifs")
        mosaic_data = MosaicJSON.from_urls(trim_urls, minzoom=14)
        mosaic_json_path = os.path.join(settings.TEMP_DIR, f"{self.vol.identifier}-mosaic.json")
        with MosaicBackend(mosaic_json_path, mosaic_def=mosaic_data) as mosaic:
            mosaic.write(overwrite=True)

        with open(mosaic_json_path, 'rb') as f:
            self.vol.mosaic_json = File(f, name=os.path.basename(mosaic_json_path))
            self.vol.save()

        logger.info(f"{self.vol.identifier} | mosaic created: {os.path.basename(mosaic_json_path)}")
        return mosaic_json_path
