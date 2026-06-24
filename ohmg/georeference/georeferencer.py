import logging
import math
import os
import sys
import time
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import List
from uuid import uuid4

import numpy as np
from django.conf import settings
from osgeo import gdal, ogr, osr

from ohmg.core.utils.srs import retrieve_srs_wkt

logger = logging.getLogger(__name__)


@dataclass
class HelmertParams:
    """The four parameters of a Helmert (similarity) transformation that maps
    image pixel/line coordinates to geographic coordinates."""

    scale: float
    # rotation in degrees, measured as an azimuth from north (the positive Y axis)
    rotation: float
    # geographic coordinates that the image origin (pixel=0, line=0) maps to
    offset_x: float
    offset_y: float

gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")

TRANSFORMATION_LOOKUP = {
    "helmert": {
        "id": "helmert",
        "gdal_code": None,
        "name": "Helmert",
        "desc": "implemented as four-parameter transformation",
    },
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


class VRTHandler:
    """This class should be given a name, and then provide
    1. the local writable path for where this VRT can be created
    2. a range request compatible http url through which the written
        file can be accessed
    3. a GDAL vsi readable url (derived from 2)

    1 and 3 are easy, but 2 is tricky to accommodate in dev and prod
    environments, specifically alongside existing pattern for
    dev/prod serving of COGs. 2 Must be a FULL url, not relative, So:

    2 (dev): This must be the LOCAL_MEDIA_HOST url pointing to uploaded/vrt
    2 (prod): This should be SITEURL pointing to uploaded/vrt."""

    def __init__(self, base_name: str, as_variant: str = None):
        self.base_name = base_name
        self.name = self.base_name

        if as_variant:
            self.set_variant_name(as_variant)

    def get_path(self):
        return Path(settings.VRT_ROOT, self.name + ".vrt")

    def get_url(self):
        base_url = (
            settings.LOCAL_MEDIA_HOST if settings.MODE == "DEV" else settings.SITEURL.rstrip("/")
        )
        return f"{base_url}{settings.VRT_URL}{self.name}.vrt"

    def get_vsi_url(self):
        return f"/vsicurl/{self.get_url()}"

    def set_variant_name(self, variant: str):
        self.name = f"{self.base_name}-{variant}"


class Georeferencer:
    def __init__(
        self,
        crs="EPSG:3857",
        transformation="poly1",
        # three different ways to add GCPs, one must be provided
        gcps_gdal: List[gdal.GCP] = [],
        gcps_geojson=None,
        gcps_points_file=None,
        verbose=False,
    ):
        # handle CRS input. crs will be used to set self.crs_code, self.crs_wkt, and self.crs_sr
        if ":" not in crs:
            raise Exception("Invalid CRS format, must be 'AUTHORITY:CODE', e.g. 'EPSG:3857'")
        self.crs_code = crs

        wkt_content = retrieve_srs_wkt(self.crs_code.split(":")[1])
        self.crs_wkt = str(wkt_content)

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
        self.gcps = []
        if len(gcps_gdal) > 0:
            self.gcps = gcps_gdal
        elif gcps_geojson:
            self._load_gcps_from_geojson(gcps_geojson)
        elif gcps_points_file:
            self._load_gcps_from_points_file(gcps_points_file)
        else:
            raise Exception("no valid gcps_* argument provided")

        # verbose can trigger extra print statements in certain contexts
        self.verbose = verbose

        self.files = {}

        self.gcps_vrt: VRTHandler = None
        self.warped_vrt: VRTHandler = None
        self.trimmed_vrt: VRTHandler = None
        self.cog: Path = None

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

    def _get_helmert_params(self) -> HelmertParams:
        """Fit a Helmert (four-parameter similarity) transformation to the GCPs
        using least squares, returning the scale, rotation, and offsets.

        The transformation maps image pixel/line coordinates to geographic
        coordinates as:

            geoX = offset_x + a * line - b * pixel
            geoY = offset_y + a * pixel + b * line

        where (a, b) = (scale * cos(angle), scale * sin(angle)). Because this is
        linear in the four unknowns (a, b, offset_x, offset_y), it can be solved
        directly from two equations per GCP -- exactly determined with two GCPs,
        and a best fit with more. This handles every orientation without any
        special-casing.
        """

        if len(self.gcps) < 2:
            raise Exception("At least two GCPs are needed to fit a Helmert transformation")

        # build two rows (the geoX and geoY equations) per GCP
        matrix, targets = [], []
        for gcp in self.gcps:
            matrix.append([gcp.GCPLine, -gcp.GCPPixel, 1, 0])
            targets.append(gcp.GCPX)
            matrix.append([gcp.GCPPixel, gcp.GCPLine, 0, 1])
            targets.append(gcp.GCPY)

        (a, b, offset_x, offset_y), *_ = np.linalg.lstsq(
            np.array(matrix, dtype=float), np.array(targets, dtype=float), rcond=None
        )

        scale = math.hypot(a, b)
        # convert the fitted angle to an azimuth in degrees from north
        rotation = (270 - math.degrees(math.atan2(b, a))) % 360

        return HelmertParams(
            scale=scale,
            rotation=rotation,
            offset_x=offset_x,
            offset_y=offset_y,
        )

    def cleanup_files(self):
        for vrt in [
            self.gcps_vrt,
            self.warped_vrt,
            self.trimmed_vrt,
        ]:
            if vrt and vrt.get_path().is_file():
                os.remove(vrt.get_path())
        if self.cog and self.cog.is_file():
            os.remove(self.cog)

    def make_gcps_vrt(
        self,
        src_path,
        out_name: str = None,
    ) -> VRTHandler:
        logger.debug(f"{Path(src_path).name} | create VRT with GCPs...")

        if not out_name:
            out_name = str(uuid4())

        self.gcps_vrt = VRTHandler(out_name, as_variant="gcps")

        if src_path.startswith("http"):
            src_path = f"/vsicurl/{src_path}"

        to = gdal.TranslateOptions(
            GCPs=self.gcps,
            format="VRT",
            creationOptions=[
                "BLOCKXSIZE=512",
                "BLOCKYSIZE=512",
            ],
        )
        try:
            gdal.Translate(str(self.gcps_vrt.get_path()), src_path, options=to)
        except Exception as e:
            logger.error(f"{src_path} | translate error: {str(e)}")
            raise e

        logger.debug(f"{Path(src_path).name} | VRT with GCPs created")

    def make_warped_vrt(
        self,
        src_path,
        out_name: str = None,
    ) -> VRTHandler:
        src_name = Path(src_path).name
        logger.debug(f"{src_name} | create warped VRT...")
        if not out_name:
            out_name = str(uuid4())

        self.make_gcps_vrt(src_path, out_name)
        self.warped_vrt = VRTHandler(out_name, as_variant="modified")

        if self.transformation["id"] == "helmert":
            ## fit the four-parameter Helmert model in one shot
            params = self._get_helmert_params()

            ## convert the rotation to arcseconds for the proj pipeline
            arcseconds = (params.rotation + 90) * 3600

            pipeline = (
                "+proj=pipeline "
                "+step +proj=axisswap +order=2,1 "
                f"+step +proj=helmert +x={params.offset_x} +y={params.offset_y} "
                f"+theta={arcseconds} +s={params.scale}"
            )

            logger.debug(f"applying: {pipeline}")

            wo = gdal.WarpOptions(
                creationOptions=[
                    "BLOCKXSIZE=512",
                    "BLOCKYSIZE=512",
                ],
                coordinateOperation=pipeline,
                format="VRT",
                dstSRS=f"{self.crs_code}",
                transformerOptions=["SRC_METHOD=NO_GEOTRANSFORM"],
                dstAlpha=True,
                resampleAlg="nearest",
            )
        else:
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
                dstAlpha=True,
                resampleAlg="nearest",
            )

        try:
            gdal.Warp(str(self.warped_vrt.get_path()), self.gcps_vrt.get_vsi_url(), options=wo)
        except Exception as e:
            logger.error(f"{self.gcps_vrt.get_vsi_url()} | warp error: {str(e)}")
            raise e

        logger.debug(f"{src_name} | warped VRT created")

    def make_trimmed_vrt(self, src_path, multimask_json_file: Path, layer_name: str):
        logger.debug(f"{Path(src_path).name} | create trimmed VRT...")

        self.make_warped_vrt(src_path)
        self.trimmed_vrt = VRTHandler(self.warped_vrt.base_name, as_variant="trim")

        wo = gdal.WarpOptions(
            format="VRT",
            dstSRS="EPSG:3857",
            cutlineDSName=multimask_json_file,
            cutlineLayer=multimask_json_file.stem,
            cutlineWhere=f"layer='{layer_name}'",
            cropToCutline=True,
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
        gdal.Warp(str(self.trimmed_vrt.get_path()), self.warped_vrt.get_vsi_url(), options=wo)

        logger.debug(f"{Path(src_path).name} | trimmed VRT created.")

    def make_cog(
        self,
        src_path,
    ) -> Path:
        a = time.time()
        logger.debug(f"{Path(src_path).name} | create COG...")

        self.make_warped_vrt(src_path)

        self.cog = Path(settings.TEMP_DIR, Path(src_path).stem + "-modified.tif")

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
            gdal.Translate(str(self.cog), self.warped_vrt.get_vsi_url(), options=to)
        except Exception as e:
            logger.error(f"{self.warped_vrt.get_vsi_url()} | translate error: {str(e)}")
            raise e

        logger.info(f"{Path(src_path).name} | COG created: {round(time.time() - a, 3)} seconds.")
