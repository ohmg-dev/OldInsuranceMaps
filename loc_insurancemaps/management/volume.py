import os
import json
import logging
from osgeo import gdal

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
    gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)

    print("building final geotiff")
    to = gdal.TranslateOptions(
        format="GTiff",
        creationOptions = [
            "TILED=YES",
            "COMPRESS=DEFLATE",
            ## the following is apparently in the COG spec but doesn't work??
            # "COPY_SOURCE_OVERVIEWS=YES",
        ],
    )

    mosaic_tif = mosaic_vrt.replace(".vrt", ".tif")
    gdal.Translate(mosaic_tif, mosaic_vrt, options=to)

    with open(mosaic_tif, 'rb') as f:
        vol.mosaic_geotiff = File(f, name=os.path.basename(mosaic_tif))
        vol.save()
