import os
import json
import logging
from osgeo import gdal

from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.backends import MosaicBackend

from django.conf import settings
from django.core.files import File

from georeference.models.resources import Layer

from loc_insurancemaps.api import CollectionConnection
from loc_insurancemaps.models import Volume
from loc_insurancemaps.utils import LOCParser, filter_volumes_for_use, unsanitize_name

logger = logging.getLogger(__name__)

def import_all_available_volumes(state, apply_filter=True, verbose=False):
    """Preparatory step that runs through all cities in the provided
    state, filters the available volumes for those cities, and then
    imports each one to create a new Volume object."""

    lc = CollectionConnection(delay=0, verbose=verbose)
    cities = lc.get_city_list_by_state(state)

    volumes = []
    for city in cities:
        lc.reset()
        city = unsanitize_name(state, city[0])
        vols = lc.get_volume_list_by_city(city, state)
        if apply_filter is True:
            vols = filter_volumes_for_use(vols)
            volumes += [i for i in vols if i['include'] is True]
        else:
            volumes += vols

    for volume in volumes:
        try:
            Volume.objects.get(pk=volume['identifier'])
        except Volume.DoesNotExist:
            import_volume(volume['identifier'])

def import_volume(identifier):

    try:
        return Volume.objects.get(pk=identifier)
    except Volume.DoesNotExist:
        pass

    lc = CollectionConnection(delay=0, verbose=True)
    response = lc.get_item(identifier)
    if response.get("status") == 404:
        return None

    parsed = LOCParser(item=response['item'], include_regions=True)
    volume_kwargs = parsed.volume_kwargs()

    # add resources to args, not in item (they exist adjacent)
    volume_kwargs["lc_resources"] = response['resources']

    volume = Volume.objects.create(**volume_kwargs)
    volume.regions.set(parsed.regions)

    return volume


def multimask_to_geojson(identifier):
    """Really, the multimask property on Volume should be reimplemented
    so it is always storing a GeoJSON FeatureCollection with the layer
    name in the properties of each feature. This helper function will
    convert the existing multimask format for now."""

    vol = Volume.objects.get(pk=identifier)
    multimask_geojson = {"type": "FeatureCollection", "features": []}
    for layer, geojson in vol.multimask.items():
        geojson["properties"] = {"layer": layer}
        multimask_geojson['features'].append(geojson)

    return multimask_geojson

def generate_mosaic_geotiff(identifier):
    """ A helpful reference from the BPLv used during the creation of this method:
    https://github.com/bplmaps/atlascope-utilities/blob/master/new-workflow/atlas-tools.py
    """

    vol = Volume.objects.get(pk=identifier)
    multimask_geojson = multimask_to_geojson(identifier)
    multimask_file_name = f"multimask-{identifier}"
    multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
    with open(multimask_file, "w") as out:
        json.dump(multimask_geojson, out, indent=1)

    trim_list = []
    for feature in multimask_geojson['features']:

        layer_name = feature['properties']['layer']
        wo = gdal.WarpOptions(
            format="VRT",
            dstSRS = "EPSG:3857",
            cutlineDSName = multimask_file,
            cutlineLayer = multimask_file_name,
            cutlineWhere = f"layer='{layer_name}'",
            cropToCutline = True,
            # creationOptions = ['COMPRESS=LZW', 'BIGTIFF=YES'],
            # resampleAlg = 'cubic',
            # dstAlpha = False,
            dstNodata = "255 255 255",
        )

        layer = Layer.objects.get(slug=layer_name)
        if not layer.file:
            raise Exception(f"no layer file for this layer {layer_name}")
        in_path = layer.file.path
        trim_name = os.path.basename(in_path).replace(".tif", "_trim.vrt")
        out_path = os.path.join(settings.TEMP_DIR, trim_name)
        gdal.Warp(out_path, in_path, options=wo)

        to = gdal.TranslateOptions(
            format="VRT",
            bandList = [1,2,3]
        )

        noalpha_path = out_path.replace(".vrt", "_noalpha.vrt")
        gdal.Translate(noalpha_path, out_path, options=to)

        trim_list.append(noalpha_path)

    mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{identifier}.vrt")
    vo = gdal.BuildVRTOptions(
        resolution = 'highest',
        outputSRS = 'EPSG:3857',
        separate = False,
        srcNodata = "255 255 255",
    )
    print("building vrt")

    use_vrt = False
    if use_vrt:
        mosaic_vrt = os.path.join("/opt/app/uploaded/mosaics", f"{identifier}.vrt")
        gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)
        print("saving VRT to volume instance")
        with open(mosaic_vrt, 'rb') as f:
            vol.mosaic_geotiff = File(f, name=os.path.basename(mosaic_vrt))
            vol.save()
        return

    mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{identifier}.vrt")
    gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)

    print("building final geotiff")
    to = gdal.TranslateOptions(
        format="GTiff",
        creationOptions = [
            "TILED=YES",
            "COMPRESS=LZW",
            "PREDICTOR=2",
            "NUM_THREADS=ALL_CPUS",
            ## the following is apparently in the COG spec but doesn't work??
            # "COPY_SOURCE_OVERVIEWS=YES",
        ],
    )

    mosaic_tif = mosaic_vrt.replace(".vrt", ".tif")
    gdal.Translate(mosaic_tif, mosaic_vrt, options=to)

    print("creating overviews")
    img = gdal.Open(mosaic_tif, 1)
    gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
    gdal.SetConfigOption("PREDICTOR", "2")
    gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
    img.BuildOverviews("AVERAGE", [2, 4, 8, 16])

    with open(mosaic_tif, 'rb') as f:
        vol.mosaic_geotiff = File(f, name=os.path.basename(mosaic_tif))
        vol.save()

def write_trim_feature_cache(feature, file_path):
    with open(file_path, "w") as f:
        json.dump(feature, f, indent=2)

def read_trim_feature_cache(file_path):
    with open(file_path, "r") as f:
        feature = json.load(f)
    return feature

def generate_mosaic_json(identifier, trim_all=False):

    vol = Volume.objects.get(pk=identifier)
    multimask_geojson = multimask_to_geojson(identifier)
    multimask_file_name = f"multimask-{identifier}"
    multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
    with open(multimask_file, "w") as out:
        json.dump(multimask_geojson, out, indent=1)

    trim_list = []
    for feature in multimask_geojson['features']:

        layer_name = feature['properties']['layer']
        wo = gdal.WarpOptions(
            format="VRT",
            dstSRS = "EPSG:3857",
            cutlineDSName = multimask_file,
            cutlineLayer = multimask_file_name,
            cutlineWhere = f"layer='{layer_name}'",
            cropToCutline = True,
            # creationOptions = ['COMPRESS=LZW', 'BIGTIFF=YES'],
            # resampleAlg = 'cubic',
            # dstAlpha = False,
            dstNodata = "255 255 255",
        )

        layer = Layer.objects.get(slug=layer_name)
        if not layer.file:
            raise Exception(f"no layer file for this layer {layer_name}")
        in_path = layer.file.path

        feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
        if os.path.isfile(feat_cache_path):
            cached_feature = read_trim_feature_cache(feat_cache_path)
        else:
            cached_feature = None
            write_trim_feature_cache(feature, feat_cache_path)

        trim_vrt_path = in_path.replace(".tif", "_trim.vrt")
        out_path = trim_vrt_path.replace(".vrt", ".tif")

        # compare this multimask feature to the cached one for this layer
        # and only (re)create a trimmed tif if they do not match
        if feature != cached_feature or trim_all is True:
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

            print(f"writing trimmed tif {os.path.basename(out_path)}")
            gdal.Translate(out_path, trim_vrt_path, options=to)
            write_trim_feature_cache(feature, feat_cache_path)

            print(f" -- building overviews")
            img = gdal.Open(out_path, 1)
            gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
            gdal.SetConfigOption("PREDICTOR", "2")
            gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
            img.BuildOverviews("AVERAGE", [2, 4, 8, 16])
        else:
            print(f"using existing trimmed tif {os.path.basename(out_path)}")

        trim_list.append(out_path)

    print(trim_list)
    trim_urls = [
        i.replace(os.path.dirname(settings.MEDIA_ROOT), settings.MEDIA_HOST.rstrip("/")) \
            for i in trim_list
    ]
    print(trim_urls)
    print("writing mosaic")
    mosaic_data = MosaicJSON.from_urls(trim_urls, minzoom=14)
    mosaic_json_path = os.path.join(settings.TEMP_DIR, f"{identifier}-mosaic.json")
    with MosaicBackend(mosaic_json_path, mosaic_def=mosaic_data) as mosaic:
        mosaic.write(overwrite=True)

    with open(mosaic_json_path, 'rb') as f:
        vol.mosaic_geotiff = File(f, name=os.path.basename(mosaic_json_path))
        vol.save()
