import os
import time
import logging
import requests
from osgeo import gdal, osr, ogr

from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import sys

logger = logging.getLogger(__name__)

class CapturingStdout(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

class CapturingStderr(list):
    def __enter__(self):
        self._stderr = sys.stderr
        sys.stderr = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
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

def get_path_variant(original_path, variant, outdir=None):
    """Used to standardize the derivative names of Document files created
    during the georeferencing process"""

    if outdir is None:
        outdir = os.path.dirname(original_path)

    basename = os.path.basename(original_path)
    ext = os.path.splitext(basename)[1]

    if variant == "gcps":
        filename = basename.replace(ext, "_gcps.vrt")
    elif variant == "VRT":
        filename = basename.replace(ext, "_modified.vrt")
    elif variant == "GTiff":
        filename = basename.replace(ext, "_modified.tif")
    else:
        raise Exception(f"unsupported derivative type: {variant}")
    
    return os.path.join(outdir, filename)

def retrieve_srs_wkt(code):

    cache_dir = ".srs_cache"
    cache_path = os.path.join(cache_dir, f"{code}-wkt.txt")
    if os.path.isfile(cache_path):
        with open(cache_path, "r") as o:
            wkt = o.read()
    else:
        url = f"https://epsg.io/{code}.wkt"
        response = requests.get(url)
        wkt = response.content.decode("utf-8")
        # with open(cache_path, "w") as o:
        #     o.write(wkt)

    return wkt

class Georeferencer(object):

    TRANSFORMATIONS = {
        "tps": {
            "id": "tps",
            "gdal_code": -1,
            "name": "Thin Plate Spline",
            "desc": "max distortion"
        },
        "poly": {
            "id": "poly",
            "gdal_code": 0,
            "name": "Highest Possible Polynomial",
            "desc": "uses highest possible polynomial order based on GCP count"
        },
        "poly1": {
            "id": "poly1",
            "gdal_code": 1,
            "name": "Polynomial 1",
            "desc": "uses polynomial 1"
        },
        "poly2": {
            "id": "poly2",
            "gdal_code": 2,
            "name": "Polynomial 2",
            "desc": "uses polynomial 2, requires 6 GCPs"
        },
        "poly3": {
            "id": "poly3",
            "gdal_code": 3,
            "name": "Polynomial 3",
            "desc": "uses polynomial 3, requires 10 GCPs (not recommended in GDAL docs)"
        }
    }

    def __init__(self,
            epsg_code=None,
            transformation=None,
            crs_code=None,
            gdal_gcps=[],
        ):

        self.gcps = gdal_gcps
        self.epsg_code = epsg_code
        self.crs_code = crs_code
        self.transformation = None
        if transformation:
            self.set_transformation(transformation)
        self.workspace = None

    def load_gcps_from_file(self, file_path):

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
                    abs(float(pixel_y))
                )
                self.gcps.append(gcp)

    def load_gcps_from_geojson(self, geo_json):

        # geo_json is assumed to be WGS84, so it must be transformed to the
        # CRS of this Georeferencer instance
        self.gcps = []

        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)
        ct = osr.CoordinateTransformation(wgs84, self.get_spatial_reference())

        for feature in geo_json['features']:

            lat = feature['geometry']['coordinates'][1]
            lng = feature['geometry']['coordinates'][0]
            point = ogr.CreateGeometryFromWkt(f"POINT ({lat} {lng})")
            point.Transform(ct)

            gcp = gdal.GCP(
                float(point.GetX()),
                float(point.GetY()),
                0,
                float(feature['properties']['image'][0]),
                float(feature['properties']['image'][1])
            )
            self.gcps.append(gcp)

    def set_transformation(self, trans_id):

        trans = self.TRANSFORMATIONS.get(trans_id)
        if trans is None:
            ids = self.TRANSFORMATIONS.keys()
            msg = f"ERROR: invalid transformation, must be one of {ids}"
            raise TypeError(msg)

        self.transformation = trans

    def set_workspace(self, directory):

        if not os.path.isdir(directory):
            os.mkdir(directory)
        self.workspace = directory

    def get_spatial_reference(self):

        sr = osr.SpatialReference()

        code = self.crs_code.split(":")[1]
        wkt = retrieve_srs_wkt(code)

        sr.ImportFromWkt(wkt)
        return sr

    def add_overviews(self, image_path):

        ## add overviews
        ## https://stackoverflow.com/a/61117295/3873885

        try:
            Image = gdal.Open(image_path, 1)
            gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
            Image.BuildOverviews("AVERAGE", [2, 4, 8, 16])
        except Exception as e:
            logger.error(e)
            raise e

    def make_warp_options(self, src_path, output_format):
        """Creates and returns a gdal WarpOptions object with the content
        gathered from self.

        out_format must be "VRT" or "GTiff".
        """

        sr_wkt = self.get_spatial_reference().ExportToWkt()

        ## if a jpg is passed in, assume that white (255, 255, 255) should be
        ## interpreted as the no data value
        src_nodata = None
        if src_path.endswith(".jpg"):
            src_nodata = "255 255 255"
        ## make WarpOptions to handle more settings in the final process
        # https://gdal.org/python/osgeo.gdal-module.html#WarpOptions
        wo = gdal.WarpOptions(
            creationOptions=[
                "TILED=YES",
                "COMPRESS=DEFLATE",
                ## the following is apparently in the COG spec but doesn't work??
                # "COPY_SOURCE_OVERVIEWS=YES",
            ],
            transformerOptions = [
                f'DST_SRS={sr_wkt}',
                f'MAX_GCP_ORDER={self.transformation["gdal_code"]}',
            ],
            format=output_format,
            dstSRS=f"{self.crs_code}",
            srcNodata=src_nodata,
            dstAlpha=True,
        )

        return wo

    def run_warp(self, dst_path, vrt_with_gcps, options):
        """Wrap the actual warping operation for debugging purposes."""

        fname = os.path.basename(dst_path)
        # with CapturingStderr() as output:
        try:
            gdal.UseExceptions()

            # f = StringIO()
            # with redirect_stderr(f):
                # do_something(my_object)

            # with CapturingStdout() as output:

            gdal.Warp(dst_path, vrt_with_gcps, options=options)
                # print(output)
            # out = f.getvalue()
            # print(out)
        except Exception as e:
            logger.error(f"{fname} | warp error: {str(e)}")

        return dst_path

    def make_gcps_vrt(self, src_path, output_directory=None):

        """This method uses gdal.Translate to put all control points into a VRT, and then
        returns that file path."""

        fname = os.path.basename(src_path)

        if output_directory is None:
            self.set_workspace(os.path.dirname(src_path))
        else:
            self.set_workspace(output_directory)

        vrt_with_gcps = get_path_variant(src_path, "gcps", outdir=self.workspace)

        to = gdal.TranslateOptions(
            GCPs=self.gcps,
            format="VRT",
        )
        try:
            gdal.Translate(vrt_with_gcps, src_path, options=to)
        except Exception as e:
            logger.error(f"{fname} | translate error: {str(e)}")
            raise e

        return vrt_with_gcps

    def make_vrt(self, src_path, output_directory=None):
        """This method uses gdal.Translate to put all control points into a VRT, and then
        returns that file path."""

        fname = os.path.basename(src_path)

        if output_directory is None:
            self.set_workspace(os.path.dirname(src_path))
        else:
            self.set_workspace(output_directory)

        vrt_with_gcps = self.make_gcps_vrt(src_path, output_directory=output_directory)
        warp_options = self.make_warp_options(src_path, "VRT")

        dst_path = get_path_variant(src_path, "VRT", outdir=output_directory)

        self.run_warp(dst_path, vrt_with_gcps, warp_options)

        if self.crs_code != "EPSG:3857":
            new_path = dst_path.replace(".vrt", "_3857.vrt")
            src_nodata = None
            if src_path.endswith(".jpg"):
                src_nodata = "255 255 255"
            new_options = gdal.WarpOptions(
                creationOptions=[
                    "TILED=YES",
                    "COMPRESS=DEFLATE",
                    ## the following is apparently in the COG spec but doesn't work??
                    # "COPY_SOURCE_OVERVIEWS=YES",
                ],
                transformerOptions = [
                    f'DST_SRS={retrieve_srs_wkt(3857)}',
                    f'MAX_GCP_ORDER={self.transformation["gdal_code"]}',
                ],
                format="VRT",
                dstSRS=f"EPSG:3857",
                srcNodata=src_nodata,
                dstAlpha=True,
            )
            gdal.Warp(new_path,dst_path,options=new_options)
            dst_path = new_path

        return dst_path


    def make_tif(self, src_path, output_directory=None):
        """This is the entry point for creating a final GeoTIFF. It calls make_gcps_vrt()
        to set the control points and then uses that VRT to generate the final file."""

        fname = os.path.basename(src_path)

        logger.debug(f"{fname} | start")
        a = time.time()

        if output_directory is None:
            self.set_workspace(os.path.dirname(src_path))
        else:
            self.set_workspace(output_directory)

        vrt_with_gcps = self.make_gcps_vrt(src_path, output_directory=output_directory)
        warp_options = self.make_warp_options(src_path, "GTiff")

        dst_path = get_path_variant(src_path, "GTiff", outdir=output_directory)

        self.run_warp(dst_path, vrt_with_gcps, warp_options)
        logger.debug(f"{fname} | warp completed in {round(time.time() - a, 3)} seconds.")

        b = time.time()
        self.add_overviews(dst_path)
        logger.debug(f"{fname} | overviews created in {round(time.time() - b, 3)} seconds.")

        logger.info(f"{fname} | georeference successful in {round(time.time() - a, 3)} seconds.")

        return dst_path
