import json
import logging
import os
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import List

from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.files import File
from django.core.files.storage import get_storage_class
from osgeo import gdal

from ohmg.core.models import Layer, LayerSet
from ohmg.core.storages import get_file_url
from ohmg.core.utils import random_alnum

from .georeferencer import Georeferencer, VRTHandler

gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
gdal.SetConfigOption("GDAL_TIFF_INTERNAL_MASK", "YES")

logger = logging.getLogger(__name__)


class Mosaicker:
    def __init__(self):
        self.multimask_file: Path = None
        self.trimmed_vrts: List[VRTHandler] = []
        self.other_vrts: List[VRTHandler] = []
        self.mosaic_vrt: VRTHandler = None
        self.cog: Path = None

    def cleanup_files(self):
        if self.multimask_file and self.multimask_file.is_file():
            os.remove(self.multimask_file)
        for i in self.trimmed_vrts:
            os.remove(i.get_path())
        for i in self.other_vrts:
            os.remove(i.get_path())
        if self.mosaic_vrt and self.mosaic_vrt.get_path().is_file():
            os.remove(self.mosaic_vrt.get_path())
        if self.cog and self.cog.is_file():
            os.remove(self.cog)

    def generate_mosaic_vrt(self, layerset) -> VRTHandler:
        """A helpful reference from the BPL used during the creation of this method:
        https://github.com/bplmaps/atlascope-utilities/blob/master/new-workflow/atlas-tools.py
        """

        multimask_geojson = layerset.multimask_geojson
        multimask_file_name = f"multimask-{layerset.category.slug}-{layerset.map.identifier}"
        self.multimask_file = Path(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
        with open(self.multimask_file, "w") as out:
            json.dump(multimask_geojson, out, indent=1)

        layer_extent_polygons = []
        for feature in multimask_geojson["features"]:
            layer_name = feature["properties"]["layer"]

            print(layer_name)
            try:
                layer = Layer.objects.get(slug=layer_name, region__document__map=layerset.map)
            except Layer.MultipleObjectsReturned as e:
                print("this layer slug matched multiple layers in this map: cancelling mosaic process")
            except Exception as  e:
                raise e

            if not layer.file:
                raise Exception(f"no layer file for this layer {layer_name}")

            if layer.extent:
                extent_poly = Polygon.from_bbox(layer.extent)
                layer_extent_polygons.append(extent_poly)

            gcpgroup = layer.region.gcpgroup
            g = Georeferencer(
                crs=f"EPSG:{gcpgroup.crs_epsg}",
                transformation=gcpgroup.transformation,
                gcps_geojson=gcpgroup.as_geojson,
            )

            g.make_trimmed_vrt(get_file_url(layer.region), self.multimask_file, layer_name)

            self.trimmed_vrts.append(g.trimmed_vrt)

            self.other_vrts.append(g.gcps_vrt)
            self.other_vrts.append(g.warped_vrt)

        if len(layer_extent_polygons) > 0:
            multi = MultiPolygon(layer_extent_polygons, srid=4326)

        bounds = multi.transform(3857, True).extent
        vo = gdal.BuildVRTOptions(
            resolution="highest",
            outputSRS="EPSG:3857",
            outputBounds=bounds,
            separate=False,
        )
        print("building vrt")

        self.mosaic_vrt = VRTHandler(f"{layerset.map.identifier}-{layerset.category.slug}")
        trim_list = [str(i.get_path()) for i in self.trimmed_vrts]
        gdal.BuildVRT(str(self.mosaic_vrt.get_path()), trim_list, options=vo)

    def generate_cog(self, layerset: LayerSet):
        start = datetime.now()

        self.generate_mosaic_vrt(layerset)

        print("building final geotiff")

        to = gdal.TranslateOptions(
            format="COG",
            creationOptions=[
                "BIGTIFF=YES",
                "COMPRESS=JPEG",
                "TILING_SCHEME=GoogleMapsCompatible",
            ],
        )
        self.cog = self.mosaic_vrt.get_path().with_suffix(".tif")
        gdal.Translate(str(self.cog), str(self.mosaic_vrt.get_path()), options=to)

        existing_file_name = layerset.mosaic_geotiff.name if layerset.mosaic_geotiff else None

        file_name = f"{layerset.map.identifier}-{layerset.category.slug}__{datetime.now().strftime('%Y-%m-%d')}__{random_alnum(6)}.tif"

        with open(self.cog, "rb") as f:
            layerset.mosaic_geotiff.save(file_name, File(f))

        storage = get_storage_class()()
        if existing_file_name and storage.exists(name=existing_file_name):
            storage.delete(name=existing_file_name)

        layerset.save(set_tilejson=True)

        print(f"completed - elapsed time: {datetime.now() - start}")

    def generate_mosaic_json(self, layerset, trim_all=False):
        """DEPRECATED: Currently, MosaicJSON is not used anywhere in the app."""
        from cogeo_mosaic.backends import MosaicBackend
        from cogeo_mosaic.mosaic import MosaicJSON

        def write_trim_feature_cache(feature, file_path):
            with open(file_path, "w") as f:
                json.dump(feature, f, indent=2)

        def read_trim_feature_cache(file_path):
            with open(file_path, "r") as f:
                feature = json.load(f)
            return feature

        logger.info(f"{layerset.vol.identifier} | generating mosaic json")

        multimask_geojson = layerset.vol.multimask_geojson
        multimask_file_name = f"multimask-{layerset.vol.identifier}"
        multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
        with open(multimask_file, "w") as out:
            json.dump(multimask_geojson, out, indent=1)

        logger.debug(f"{layerset.vol.identifier} | multimask loaded")
        logger.info(f"{layerset.vol.identifier} | iterating and trimming layers")
        trim_list = []
        for feature in multimask_geojson["features"]:
            layer_name = feature["properties"]["layer"]
            layer = Layer.objects.get(slug=layer_name)
            if not layer.file:
                logger.error(
                    f"{layerset.vol.identifier} | no layer file for this layer {layer_name}"
                )
                raise Exception(f"no layer file for this layer {layer_name}")
            in_path = layer.file.path

            layer_dir = os.path.dirname(in_path)
            file_name = os.path.basename(in_path)
            logger.debug(f"{layerset.vol.identifier} | processing layer file {file_name}")

            file_root = os.path.splitext(file_name)[0]
            existing_trimmed_tif = glob.glob(f"{layer_dir}/{file_root}*_trim.tif")
            print(existing_trimmed_tif)

            feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
            if os.path.isfile(feat_cache_path):
                cached_feature = read_trim_feature_cache(feat_cache_path)
                logger.debug(f"{layerset.vol.identifier} | using cached trim json boundary")
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
                    dstSRS="EPSG:3857",
                    cutlineDSName=multimask_file,
                    cutlineLayer=multimask_file_name,
                    cutlineWhere=f"layer='{layer_name}'",
                    cropToCutline=True,
                    creationOptions=["COMPRESS=LZW", "BIGTIFF=YES"],
                    resampleAlg="cubic",
                    dstAlpha=False,
                    dstNodata="255 255 255",
                )
                gdal.Warp(trim_vrt_path, in_path, options=wo)

                to = gdal.TranslateOptions(
                    format="GTiff",
                    bandList=[1, 2, 3],
                    creationOptions=[
                        "TILED=YES",
                        "COMPRESS=LZW",
                        "PREDICTOR=2",
                        "NUM_THREADS=ALL_CPUS",
                        ## the following is apparently in the COG spec but doesn't work??
                        # "COPY_SOURCE_OVERVIEWS=YES",
                    ],
                )

                logger.debug(f"writing trimmed tif {os.path.basename(out_path)}")
                gdal.Translate(out_path, trim_vrt_path, options=to)
                write_trim_feature_cache(feature, feat_cache_path)

                img = gdal.Open(out_path, 1)
                if img is None:
                    logger.warning(
                        f"{layerset.vol.identifier} | file was not properly created, omitting: {file_name}"
                    )
                    continue
                logger.debug(f"{layerset.vol.identifier} | building overview: {file_name}")
                gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
                gdal.SetConfigOption("PREDICTOR", "2")
                gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
                img.BuildOverviews("AVERAGE", [2, 4, 8, 16])

            else:
                logger.debug(f"{layerset.vol.identifier} | using existing trimmed tif {file_name}")

            trim_list.append(out_path)

        trim_urls = [
            i.replace(os.path.dirname(settings.MEDIA_ROOT), settings.LOCAL_MEDIA_HOST.rstrip("/"))
            for i in trim_list
        ]
        logger.info(
            f"{layerset.vol.identifier} | writing mosaic from {len(trim_urls)} trimmed tifs"
        )
        mosaic_data = MosaicJSON.from_urls(trim_urls, minzoom=14)
        mosaic_json_path = os.path.join(settings.TEMP_DIR, f"{layerset.vol.identifier}-mosaic.json")
        with MosaicBackend(mosaic_json_path, mosaic_def=mosaic_data) as mosaic:
            mosaic.write(overwrite=True)

        with open(mosaic_json_path, "rb") as f:
            layerset.vol.mosaic_json = File(f, name=os.path.basename(mosaic_json_path))
            layerset.vol.save()

        logger.info(
            f"{layerset.vol.identifier} | mosaic created: {os.path.basename(mosaic_json_path)}"
        )
        return mosaic_json_path
