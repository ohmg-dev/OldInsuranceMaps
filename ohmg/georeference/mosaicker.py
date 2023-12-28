import os
import json
import glob
from datetime import datetime
import logging
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.profiles import DefaultGTiffProfile

from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.backends import MosaicBackend

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.core.files import File

from ohmg.georeference.models import Layer
from ohmg.utils import (
    random_alnum,
)

from ohmg.loc_insurancemaps.models import Volume

logger = logging.getLogger(__name__)

def calculate_tranform_info(extent):
    width = abs(int(extent[2] - extent[0]))
    height = abs(int(extent[3] - extent[1]))
    transform = rasterio.transform.from_bounds(
        extent[0],
        extent[1],
        extent[2],
        extent[3],
        width=width,
        height=height,
    )
    return (width, height, transform)

def write_trim_feature_cache(feature, file_path):
    with open(file_path, "w") as f:
        json.dump(feature, f, indent=2)

def read_trim_feature_cache(file_path):
    with open(file_path, "r") as f:
        feature = json.load(f)
    return feature

def create_rasterio_dataset(data, crs, transform):
    # Receives a 2D array, a transform and a crs to create a rasterio dataset
    memfile = MemoryFile()
    dataset = memfile.open(
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=3,
        crs=crs, 
        transform=transform,
        dtype=data.dtype,
        interleave='band',
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress='lzw',
    )
    dataset.write(data)

    return dataset


def make_mosaicjson(identifier, trim_all=False):
    """
    """

    vol = Volume.objects.get(pk=identifier)

    start = datetime.now()

    logger.info(f"{identifier} | GENERATE MosaicJSON")

    multimask_geojson = vol.get_multimask_geojson()

    ct_4326_3857 = CoordTransform(SpatialReference(4326), SpatialReference(3857))

    trim_list = []
    cleanup_list = []
    for feature in multimask_geojson['features']:

        mask_geom = Polygon(feature['geometry']['coordinates'][0], srid=4326)
        mask_geojson = json.loads(mask_geom.transform(ct_4326_3857, True).json)

        layer_name = feature['properties']['layer']

        layer = Layer.objects.get(slug=layer_name)
        if not layer.file:
            raise Exception(f"no layer file for this layer {layer_name}")

        in_path = layer.file.path
        layer_dir = os.path.dirname(in_path)
        file_name = os.path.basename(in_path)
        logger.debug(f"{identifier} | processing layer file {file_name}")

        file_root = os.path.splitext(file_name)[0]

        feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
        if os.path.isfile(feat_cache_path):
            cached_feature = read_trim_feature_cache(feat_cache_path)
            logger.debug(f"{identifier} | using cached trim json boundary")
        else:
            cached_feature = None
            write_trim_feature_cache(feature, feat_cache_path)

        # compare this multimask feature to the cached one for this layer
        # and only (re)create a trimmed tif if they do not match
        if feature != cached_feature or trim_all is True:
            
            # get list of existing files before creating the new one
            cleanup_list += glob.glob(f"{layer_dir}/{file_root}*_trim.tif")

            unique_id = random_alnum(6)
            trimmed_tif_path = in_path.replace(".tif", f"{file_root}_{unique_id}_trim.tif")

            logger.debug(f"{identifier} | trimming tif {file_name}")
            with rasterio.open(in_path, "r") as src:
                out_image, out_transform = mask(src, [mask_geojson], nodata=255, indexes=[1,2,3])
                with rasterio.open(trimmed_tif_path, "w",
                    driver="GTiff",
                    width=out_image.shape[2],
                    height=out_image.shape[1],
                    transform=out_transform,
                    count=3,
                    dtype='uint8',
                    crs="EPSG:3857",
                    nodata=255,
                    interleave='band',
                    tiled=True,
                    blockxsize=256,
                    blockysize=256,
                    compress='lzw',
                ) as trim_temp:
                    trim_temp.write(out_image)

                with rasterio.open(trimmed_tif_path, "r+") as f:
                    f.build_overviews([2,4,8,16], Resampling.nearest)
                write_trim_feature_cache(feature, feat_cache_path)
                del out_image
            trim_list.append(trimmed_tif_path)
        else:
            existing_tif = glob.glob(f"{layer_dir}/{file_root}*_trim.tif")
            trim_list.append(existing_tif[0])
            logger.info(f"{identifier} | using existing trimmed tif, mask feature unchanged")

    if len(trim_list) > 0:
        trim_urls = [
            i.replace(os.path.dirname(settings.MEDIA_ROOT), settings.MEDIA_HOST.rstrip("/")) \
                for i in trim_list
        ]
        logger.info(f"{identifier} | writing mosaic from {len(trim_urls)} trimmed tifs")
        mosaic_data = MosaicJSON.from_urls(trim_urls, minzoom=14)

        if vol.mosaic_json:
            cleanup_list.append(vol.mosaic_json.path)

        cleanup_list += glob.glob(f"{settings.TEMP_DIR}/{identifier}-*-mosaic.json")

        rand = random_alnum(6)
        mosaic_json_path = os.path.join(settings.TEMP_DIR, f"{identifier}-{rand}-mosaic.json")
        with MosaicBackend(mosaic_json_path, mosaic_def=mosaic_data) as mosaic:
            mosaic.write(overwrite=True)

        with open(mosaic_json_path, 'rb') as f:
            vol.mosaic_json = File(f, name=os.path.basename(mosaic_json_path))
            vol.save()

        for i in cleanup_list:
            os.remove(i)

        logger.info(f"{identifier} | mosaic created: {os.path.basename(mosaic_json_path)}")
    else:
        logger.info(f"{identifier} | no updates made to mmosaic")

    print(f"{identifier} | COMPLETE: elapsed time = {datetime.now()-start}")

def make_geotiff(identifier, trim_all=False):
    """
    This should be rewritten following some of the merge patterns here:
    https://medium.com/analytics-vidhya/python-for-geosciences-raster-merging-clipping-and-reprojection-with-rasterio-9f05f012b88a
    """

    vol = Volume.objects.get(pk=identifier)
    create_new = False
    if not vol.mosaic_geotiff or trim_all is True:
        create_new = True

    start = datetime.now()

    logger.info(f"{identifier} | GENERATE GEOTIFF MOSAIC: from scratch = {create_new}")

    ## if create_new is True (or trim_all is True), then new trimmed tifs will be
    ## made for each layer and then merged at the end.

    ## if create_new is False, then only the layers whose masks have been altered
    ## (or newly created) will be trimmed, and then merged one by one into the
    ## existing GeoTIFF for this volume.

    multimask_geojson = vol.get_multimask_geojson()

    out_geotiff_path = os.path.join(settings.TEMP_DIR, f"{identifier}-mosaic.tif")

    ct = CoordTransform(SpatialReference(4326), SpatialReference(3857))

    # with rasterio.open("./merged.tif", "w", **profile) as mainfile:

    merge_tifs = []
    tif_extents = []
    for feature in multimask_geojson['features']:

        mask_geom = Polygon(feature['geometry']['coordinates'][0], srid=4326)
        mask_geojson = json.loads(mask_geom.transform(ct, True).json)

        layer_name = feature['properties']['layer']
        print(layer_name)

        layer = Layer.objects.get(slug=layer_name)
        if not layer.file:
            raise Exception(f"no layer file for this layer {layer_name}")

        if layer.extent:
            extent_poly = Polygon.from_bbox(layer.extent)
            tif_extents.append(extent_poly)

        in_path = layer.file.path

        file_name = os.path.basename(in_path)
        logger.debug(f"{identifier} | processing layer file {file_name}")

        feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
        if os.path.isfile(feat_cache_path):
            cached_feature = read_trim_feature_cache(feat_cache_path)
            logger.debug(f"{identifier} | using cached trim json boundary")
        else:
            cached_feature = None
            write_trim_feature_cache(feature, feat_cache_path)

        trimmed_tif_path = in_path.replace(".tif", "_trim.tif")

        # compare this multimask feature to the cached one for this layer
        # and only (re)create a trimmed tif if they do not match
        if feature != cached_feature or trim_all is True:
        # if feature != cached_feature or not os.path.isfile(trimmed_tif_path) or trim_all is True:

            logger.debug(f"{identifier} | trimming tif {file_name}")
            with rasterio.open(in_path, "r") as src:
                out_image, out_transform = mask(src, 
                                                [mask_geojson],
                                                #  nodata=255, indexes=[1,2,3]
                                                 )

                # mask_dataset = create_rasterio_dataset(out_image, src.crs, out_transform)

                # merge_tifs.append(mask_dataset)
                write_trim_feature_cache(feature, feat_cache_path)
                m_height = out_image.shape[1]
                m_width = out_image.shape[2]

                with rasterio.open(trimmed_tif_path, "w",
                    width=m_width,
                    height=m_height,
                    transform=out_transform,
                    count=4,
                    dtype='uint8',
                    crs="EPSG:3857",

                    # nodata=255,
                    driver="GTiff",
                    interleave='pixel',
                    tiled=True,
                    blockxsize=512,
                    blockysize=512,
                    compress='deflate',
                    predictor=2,

                    # driver="COG",
                    # compress="jpeg",
                ) as trim_temp:
                    trim_temp.write(out_image)
                del out_image
            merge_tifs.append(trimmed_tif_path)
        else:
            logger.info(f"{identifier} | skipping {file_name}, mask feature unchanged")

    multi = MultiPolygon(tif_extents, srid=4326)
    extent = multi.transform(3857, True).extent
    

    # Construct rasterio transform object using x and y coordiantes
    width, height, transform = calculate_tranform_info(extent)

    profile = DefaultGTiffProfile()
    profile.update(
        crs="EPSG:3857",
        width=width,
        height=height,
        transform=transform,
        count=3,
        nodata=255,
    )
    print(profile)

    if len(merge_tifs) > 0:
        logger.info(f"{identifier} | merging {len(merge_tifs)} trimmed layers")

        if create_new:
            ## run a merge if there are two or more layers
            if len(merge_tifs) > 1:
                trimmed_open = [rasterio.open(f, "r") for f in merge_tifs]
                merge(trimmed_open, nodata=255, indexes=[1,2,3], dst_path=out_geotiff_path)
                [i.close() for i in trimmed_open]
                # merged, merged_transform = merge(merge_tifs, nodata=255, indexes=[1,2,3], dst_path=out_geotiff_path)
            # merged, merged_transform = merge(merge_tifs, nodata=255, indexes=[1,2,3])

            
            # otherwise just copy the single file over to be the geotiff mosaic for this item
            elif len(merge_tifs) == 1:
                with open(merge_tifs[0], 'rb') as f:
                    vol.mosaic_geotiff.save(os.path.basename(out_geotiff_path), File(f), save=True)

        else:
            ## merge in the newly altered tifs to the existing geotiff for the item
            trimmed_open = [rasterio.open(f, "r") for f in merge_tifs]
            with rasterio.open(vol.mosaic_geotiff.path, "r") as existing_tif:
                merged, merged_transform = merge(merge_tifs + [existing_tif], nodata=255,
                                                 indexes=[1,2,3], dst_path=out_geotiff_path)
            [i.close() for i in trimmed_open]
            # for mt in merge_tifs:
            #     with rasterio.open(mt, "r"):

        # print("writing merged data")
        # with rasterio.open(out_geotiff_path, "w",
        #     driver="GTiff",
        #     width=merged.shape[2],
        #     height=merged.shape[1],
        #     transform=merged_transform,
        #     count=3,
        #     dtype='uint8',
        #     crs="EPSG:3857",
        #     nodata=255,
        #     interleave='band',
        #     tiled=True,
        #     blockxsize=256,
        #     blockysize=256,
        #     compress='deflate',
        # ) as dst: 
        #     dst.write(merged)

        with open(out_geotiff_path, 'rb') as f:
            vol.mosaic_geotiff.save(os.path.basename(out_geotiff_path), File(f), save=True)
        os.remove(out_geotiff_path)

        ## finally, build overviews
        print(f"{identifier} | building overviews...")
        with rasterio.open(vol.mosaic_geotiff.path, "r+") as out_tiff:
            out_tiff.build_overviews([2,4,8,16], Resampling.nearest)


    print(f"{identifier} | COMPLETE: elapsed time = {datetime.now()-start}")
    # print("merging")
    # for i in trimmed:
    #     print(type(i))
    # # merged, merged_transform = merge(trimmed, nodata=255, indexes=[1,2,3], dst_path="./merged.tif")
    # with rasterio.open("./merged.tif", "w", transform=out_transform) as output:
    #     for i in trimmed:
    #         output.write(i)
    # with rasterio.open(, "w", driver="GTiff") as output:
    #     print("writing merged file")
    #     for n, ar in enumerate(merged):
    #         output.write(ar, n)

        # with MemoryFile as memfile:


        # trim_name = os.path.basename(in_path).replace(".tif", "_trim.vrt")
    #     out_path = os.path.join(settings.TEMP_DIR, trim_name)
    #     gdal.Warp(out_path, in_path, options=wo)

    #     to = gdal.TranslateOptions(
    #         format="VRT",
    #         bandList = [1,2,3]
    #     )

    #     noalpha_path = out_path.replace(".vrt", "_noalpha.vrt")
    #     gdal.Translate(noalpha_path, out_path, options=to)

    #     trim_list.append(noalpha_path)

    # mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{identifier}.vrt")
    # vo = gdal.BuildVRTOptions(
    #     resolution = 'highest',
    #     outputSRS = 'EPSG:3857',
    #     separate = False,
    #     srcNodata = "255 255 255",
    # )
    # print("building vrt")

    # use_vrt = False
    # if use_vrt:
    #     mosaic_vrt = os.path.join("/opt/app/uploaded/mosaics", f"{identifier}.vrt")
    #     gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)
    #     print("saving VRT to volume instance")
    #     with open(mosaic_vrt, 'rb') as f:
    #         vol.mosaic_geotiff = File(f, name=os.path.basename(mosaic_vrt))
    #         vol.save()
    #     return

    # mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{identifier}.vrt")
    # gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)

    # print("building final geotiff")
    # to = gdal.TranslateOptions(
    #     format="GTiff",
    #     creationOptions = [
    #         "TILED=YES",
    #         "COMPRESS=LZW",
    #         "PREDICTOR=2",
    #         "NUM_THREADS=ALL_CPUS",
    #         ## the following is apparently in the COG spec but doesn't work??
    #         # "COPY_SOURCE_OVERVIEWS=YES",
    #     ],
    # )

    # mosaic_tif = mosaic_vrt.replace(".vrt", ".tif")
    # gdal.Translate(mosaic_tif, mosaic_vrt, options=to)

    # ## for some reason, creating overviews and then saving the file to
    # ## django's filefield with
    # ## with open(mosaic_tif, 'rb') as f:
    # ##    vol.mosaic_geotiff.save(os.path.basename(mosaic_tif), File(f), save=True)
    # ## seems to make an empty tiff... (still need to figure out why...)
    # ## for now, save to django without overviews.
    # ## however, Titiler is still returning empty tiles...

    # with open(mosaic_tif, 'rb') as f:
    #     vol.mosaic_geotiff.save(os.path.basename(mosaic_tif), File(f), save=True)

    # print("creating overviews")
    # img = gdal.Open(vol.mosaic_geotiff.path, 1)
    # gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
    # gdal.SetConfigOption("PREDICTOR", "2")
    # gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
    # img.BuildOverviews("AVERAGE", [2, 4, 8, 16])
