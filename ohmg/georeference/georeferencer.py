import os
import sys
import time
import logging
import requests
from pathlib import Path
from uuid import uuid4

from osgeo import gdal, osr, ogr

from io import StringIO

from django.conf import settings

logger = logging.getLogger(__name__)

gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")

TRANSFORMATION_LOOKUP = {
    "tps": {
        "id": "tps",
        "gdal_code": -1,
        "name": "Thin Plate Spline",
        "desc": "max distortion",
    },
    "poly": {
        "id": "poly",
        "gdal_code": 0,
        "name": "Highest Possible Polynomial",
        "desc": "uses highest possible polynomial order based on GCP count",
    },
    "poly1": {
        "id": "poly1",
        "gdal_code": 1,
        "name": "Polynomial 1",
        "desc": "uses polynomial 1",
    },
    "poly2": {
        "id": "poly2",
        "gdal_code": 2,
        "name": "Polynomial 2",
        "desc": "uses polynomial 2, requires 6 GCPs",
    },
    "poly3": {
        "id": "poly3",
        "gdal_code": 3,
        "name": "Polynomial 3",
        "desc": "uses polynomial 3, requires 10 GCPs (not recommended in GDAL docs)",
    },
}


class CapturingStdout(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


class CapturingStderr(list):
    def __enter__(self):
        self._stderr = sys.stderr
        sys.stderr = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stderr = self._stderr


## DEPRECATED - this was a fun idea, but polynomial 2 and beyond create
## crazy results, so only polynomial 1 is used throughout the app for now.
def anticipate_polynomial_order(gcp_count):
    """If the 'poly' transformation has been chosen, then the actual
    polynomial order that is used by GDAL will depend on the number of
    GCPs that are provided.
    3-5 GCPs: poly1
    6-9 GCPs: poly2
    10+ GCPs: poly3 (though this isn't recommended in the gdal docs)
    Thus, to know after the fact which one GDAL has chosen, we will
    preemptively set it here based on the criteria above.
    """

    if gcp_count < 6:
        return "poly1"
    elif gcp_count < 10:
        return "poly2"
    else:
        ## based on recs from GDAL docs, use poly2 here even
        ## though there are enough GCPs for poly3
        return "poly3"


def retrieve_srs_wkt(code):
    srs_cache_dir = os.path.join(settings.CACHE_DIR, "srs_wkt")
    if not os.path.isdir(srs_cache_dir):
        os.makedirs(srs_cache_dir, exist_ok=True)
    cache_path = os.path.join(srs_cache_dir, f"{code}-wkt.txt")
    if os.path.isfile(cache_path):
        with open(cache_path, "r") as o:
            wkt = o.read()
    else:
        url = f"https://epsg.io/{code}.wkt"
        response = requests.get(url)
        wkt = response.content.decode("utf-8")
        with open(cache_path, "w") as o:
            o.write(wkt)

    return wkt


class Georeferencer:
    def __init__(
        self,
        crs="EPGS:3857",
        transformation="poly1",
        # three different ways to add GCPs, one must be provided
        gcps_gdal=None,
        gcps_geojson=None,
        gcps_points_file=None,
        verbose=False,
    ):
        # handle CRS input. crs will be used to set self.crs_code, self.crs_wkt, and self.crs_sr
        if ":" not in crs:
            raise Exception("Invalid CRS format, must be 'AUTHORITY:CODE', e.g. 'EPSG:3857'")
        self.crs_code = crs

        self.crs_wkt = retrieve_srs_wkt(self.crs_code.split(":")[1])

        sr = osr.SpatialReference()
        sr.ImportFromWkt(self.crs_wkt)
        self.crs_sr = sr

        # handle the input transformation
        self.transformation = TRANSFORMATION_LOOKUP.get(transformation)
        if self.transformation is None:
            msg = f"ERROR: invalid transformation, must be one of {TRANSFORMATION_LOOKUP.keys()}"
            raise TypeError(msg)

        # handle the input GCPs to GDAL GCPs, method depends on the input
        # format. self.gcps should be a list of gdal.GCP objects.
        if gcps_gdal:
            self.gcps = gcps_gdal
        elif gcps_geojson:
            self._load_gcps_from_geojson(gcps_geojson)
        elif gcps_points_file:
            self._load_gcps_from_points_file(gcps_points_file)
        else:
            raise Exception("no valid gcps_* argument provided")

        # verbose can trigger extra print statements in certain contexts
        self.verbose = verbose

        if self.verbose:
            print("initialized")

    def _load_gcps_from_file(self, file_path):
        z = 0
        with open(file_path, "r") as f:
            for line in f.readlines():
                if line.startswith("mapX"):
                    continue
                items = line.split(",")
                if len(items) == 1:
                    items = items[0].split()
                try:
                    long, lat, pixel_x, pixel_y = items[:4]
                except ValueError:
                    raise Exception("Malformed .points file.")
                gcp = gdal.GCP(
                    float(long),
                    float(lat),
                    z,
                    float(pixel_x),
                    # need to take the absolute value of this pixel coord
                    abs(float(pixel_y)),
                )
                self.gcps.append(gcp)

    def _load_gcps_from_geojson(self, geo_json):
        # geo_json is assumed to be WGS84, so it must be transformed to the
        # CRS of this Georeferencer instance
        self.gcps = []

        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)
        ct = osr.CoordinateTransformation(wgs84, self.crs_sr)

        for feature in geo_json["features"]:
            lat = feature["geometry"]["coordinates"][1]
            lng = feature["geometry"]["coordinates"][0]
            point = ogr.CreateGeometryFromWkt(f"POINT ({lat} {lng})")
            point.Transform(ct)

            gcp = gdal.GCP(
                float(point.GetX()),
                float(point.GetY()),
                0,
                float(feature["properties"]["image"][0]),
                float(feature["properties"]["image"][1]),
            )
            self.gcps.append(gcp)

    def make_gcps_vrt(
        self,
        src_path,
        out_name: str = None,
    ):
        logger.debug(f"{Path(src_path).name} | create VRT with GCPs...")

        if not out_name:
            out_name = str(uuid4())

        if src_path.startswith("http"):
            src_path = f"/vsicurl/{src_path}"

        out_name = f"{out_name}-gcps.vrt"

        read_out_path = f"{settings.MEDIA_HOST.rstrip('/')}{settings.MEDIA_URL}vrt/{out_name}"
        write_out_path = Path(settings.OHMG_VRT_DIR, out_name)

        to = gdal.TranslateOptions(
            GCPs=self.gcps,
            format="VRT",
            creationOptions=[
                "BLOCKXSIZE=512",
                "BLOCKYSIZE=512",
            ],
        )
        try:
            gdal.Translate(str(write_out_path), src_path, options=to)
        except Exception as e:
            logger.error(f"{src_path} | translate error: {str(e)}")
            raise e

        logger.debug(f"{Path(src_path).name} | VRT with GCPs created")

        return (read_out_path, write_out_path)

    def make_warped_vrt(
        self,
        src_path,
        out_name: str = None,
    ):
        logger.debug(f"{Path(src_path).name} | create warped VRT...")
        if not out_name:
            out_name = str(uuid4())
        read_gcps_vrt, write_gcps_vrt = self.make_gcps_vrt(src_path, out_name)

        if read_gcps_vrt.startswith("http"):
            read_gcps_vrt = f"/vsicurl/{read_gcps_vrt}"

        out_name = f"{out_name}-modified.vrt"
        read_out_path = f"{settings.MEDIA_HOST.rstrip('/')}{settings.MEDIA_URL}vrt/{out_name}"
        write_out_path = Path(settings.OHMG_VRT_DIR, out_name)

        wo = gdal.WarpOptions(
            creationOptions=[
                #     "NUM_THREADS=ALL_CPUS",
                #     ## originally used this set of flags used
                #     # "COMPRESS=DEFLATE",
                #     ## should have been used PREDICTOR=2 with DEFLATE but didn't know about it
                #     # "PREDICTOR=2"
                #     ## useful in general but not needed when using COG driver
                "BLOCKXSIZE=512",
                "BLOCKYSIZE=512",
                #     ## advisable if using JPEG with GTiff, but not supported in COG
                #     # "JPEG_QUALITY=75",
                #     # "PHOTOMETRIC=YCBCR",
                #     ## Use JPEG, as recommended by Paul Ramsey article:
                #     ## https://blog.cleverelephant.ca/2015/02/geotiff-compression-for-dummies.html
                # "COMPRESS=JPEG",
            ],
            transformerOptions=[
                f"DST_SRS={self.crs_wkt}",
                f'MAX_GCP_ORDER={self.transformation["gdal_code"]}',
            ],
            format="VRT",
            dstSRS=f"{self.crs_code}",
            # srcNodata=src_nodata,
            # srcAlpha=True,
            dstAlpha=True,
            resampleAlg="nearest",
        )
        try:
            gdal.Warp(str(write_out_path), read_gcps_vrt, options=wo)
        except Exception as e:
            logger.error(f"{read_gcps_vrt} | warp error: {str(e)}")
            raise e

        logger.debug(f"{Path(src_path).name} | warped VRT created")

        return (read_out_path, write_out_path)

    def make_cog(
        self,
        src_path,
    ):
        a = time.time()
        logger.debug(f"{Path(src_path).name} | create COG...")

        read_modified_vrt, write_modified_vrt = self.make_warped_vrt(src_path)
        if read_modified_vrt.startswith("http"):
            read_modified_vrt = f"/vsicurl/{read_modified_vrt}"

        write_out_path = Path(settings.TEMP_DIR, Path(src_path).stem + "-modified.tif")

        to = gdal.TranslateOptions(
            # format="GTiff",
            format="COG",
            # maskBand="mask",
            creationOptions=[
                # 'COMPRESS=DEFLATE',
                # 'PREDICTOR=2',
                "COMPRESS=JPEG",
                # 'TILED=YES',
                # 'BLOCKXSIZE=512',
                # 'BLOCKYSIZE=512',
                # "PHOTOMETRIC=YCBCR",
                "TILING_SCHEME=GoogleMapsCompatible",
            ],
            resampleAlg="nearest",
        )
        try:
            gdal.Translate(str(write_out_path), read_modified_vrt, options=to)
        except Exception as e:
            logger.error(f"{read_modified_vrt} | translate error: {str(e)}")
            raise e

        logger.info(f"{Path(src_path).name} | COG created: {round(time.time() - a, 3)} seconds.")

        return write_out_path
