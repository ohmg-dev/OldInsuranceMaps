import logging
import math
import os
import sys
import time
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Union
from uuid import uuid4

from django.conf import settings
from osgeo import gdal, ogr, osr

from ohmg.core.utils.srs import retrieve_srs_wkt

from .geometry import azimuth_from_coords

logger = logging.getLogger(__name__)

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

    def _calculate_scale(self) -> float:
        """Compares two GCPs and returns a scale factor."""

        if len(self.gcps) < 2:
            raise Exception("At least GCPs are needed to calculate a scale factor")

        gcp1, gcp2 = self.gcps[0], self.gcps[1]

        # distance between the geographic coords in each GCP
        # this distance is absolute so the order of the coords doesn't matter
        geo_dist = math.dist(
            (gcp1.GCPX, gcp1.GCPY),
            (gcp2.GCPX, gcp2.GCPY),
        )

        # distance between the pixel coords in each GCP
        # this distance is absolute so the order of the coords doesn't matter
        img_dist = math.dist(
            (gcp1.GCPPixel, gcp1.GCPLine),
            (gcp2.GCPPixel, gcp2.GCPLine),
        )

        return geo_dist / img_dist

    def _calculate_rotation(self, img_height: Union[float, None] = None) -> float:
        """Compares two GCPs and calculates the difference in the angles
        between the geometric points and the pixel points.

        Returns the angle in degrees from 'north', i.e. the positive Y axis"""

        if len(self.gcps) < 2:
            raise Exception("At least two GCPs are needed to calculate a scale factor")

        # sort the GCPs so they are ordered from lowest to highest,
        # then right to left, as they appear on the source image.
        # this allows us to figure out the orientation
        self.gcps.sort(key=lambda x: x.GCPPixel)
        self.gcps.sort(key=lambda x: x.GCPLine, reverse=True)

        # make sure img height is set because it is needed to properly
        # handle the inverted Y coords.
        if not img_height:
            ds = gdal.Open(self.gcps_vrt.get_vsi_url())
            img_height = ds.RasterYSize
        img_coords = [(i.GCPPixel, img_height - i.GCPLine) for i in self.gcps]
        img_azimuth = azimuth_from_coords(img_coords)

        geo_coords = [(i.GCPX, i.GCPY) for i in self.gcps]
        geo_azimuth = azimuth_from_coords(geo_coords)

        difference = geo_azimuth - img_azimuth
        return difference

    def _calculate_helmert_offsets(self, scale: float, rotation: float) -> Tuple[float, float]:
        """Calculates the x and y offsets needed for helmert transformation, based
        on GCP
        """

        ## get the gcp that is closest to the top of the page
        use_gcp = min(self.gcps, key=lambda x: x.GCPPixel)

        ## use the scale factor to calculate the real distance to page extent
        dist_to_page_edge = use_gcp.GCPLine * scale
        dist_to_page_top = use_gcp.GCPPixel * scale

        ## rotation is azimuth, i.e. degrees from positive y-axis,
        ## must adjust to be degrees from positive x-axis
        theta1 = 90 - rotation
        ## further adjustments to normalize
        if theta1 < 0:
            theta1 += 180
        if theta1 > 180:
            theta1 -= 180

        ## calculate the target angle q, the angle from the GCP coord
        ## to the top left corner of the image, relative to negative
        ## x-axis
        r_degrees = 180 - (90 + theta1)
        r_radians = math.radians(r_degrees)
        s_radians = math.atan(dist_to_page_edge / dist_to_page_top)
        q_radians = r_radians + s_radians

        ## get the real distance between the GCP coord and the page corner
        dist_to_page_corner = math.sqrt(dist_to_page_edge**2 + dist_to_page_top**2)

        ## calculate the offset distances using q angle and distance from
        ## GCP to page corner as hypotenuse
        x_offset = math.cos(q_radians) * dist_to_page_corner
        y_offset = math.sin(q_radians) * dist_to_page_corner

        ## adjust the GCP's coords by adding/subtracting the offsets based
        ## on whether the top of the page is above or below the x-axis
        if abs(rotation) > 90:
            dx = use_gcp.GCPX + x_offset
            dy = use_gcp.GCPY - y_offset
        else:
            dx = use_gcp.GCPX - x_offset
            dy = use_gcp.GCPY + y_offset

        return (dx, dy)

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

        if len(self.gcps) == 2 and self.transformation["id"] == "helmert":
            ## get scale factor
            scale = self._calculate_scale()

            ## get rotation
            rotation = self._calculate_rotation()
            ## adjust and convert to arcseconds
            arcseconds = (rotation + 90) * 3600

            ## get the x y offsets
            dx, dy = self._calculate_helmert_offsets(scale, rotation)

            pipeline = (
                "+proj=pipeline "
                "+step +proj=axisswap +order=2,1 "
                f"+step +proj=helmert +x={dx} +y={dy} +theta={arcseconds} +s={scale}"
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
