import os
import time
from osgeo import gdal, osr

from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import sys

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



## making a geoserver layer out of the newly georeferenced image, something like
# from geonode.layers.utils import file_upload
# layer = file_upload(output_file_path)

def georeference_document(document, transformation="poly", user=None, gcp_group=None):

    if gcp_group is None:
        try:
            gcp_group = GCPGroup.objects.get(document=document)
        except GCPGroup.DoesNotExist as exception:
            raise exception

    g = Georeferencer(
        gdal_gcps=gcp_group.gdal_gcps,
        transformation=transformation,
        out_dir=settings.TEMP_DIR,
        crs=gcp_group.crs_epsg
    )

    output = g.georeference(document.doc_file.path)
    print(output)

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

class Georeferencer(object):

    trans_options = [
        {
            "id": "tps",
            "gdal_code": -1,
            "name": "Thin Plate Spline",
            "desc": "max distortion"
        },
        {
            "id": "poly",
            "gdal_code": 0,
            "name": "Highest Possible Polynomial",
            "desc": "uses highest possible polynomial order based on GCP count"
        },
        {
            "id": "poly1",
            "gdal_code": 1,
            "name": "Polynomial 1",
            "desc": "uses polynomial 1"
        },
        {
            "id": "poly2",
            "gdal_code": 2,
            "name": "Polynomial 2",
            "desc": "uses polynomial 2, requires 6 GCPs"
        },
        {
            "id": "poly3",
            "gdal_code": 3,
            "name": "Polynomial 3",
            "desc": "uses polynomial 3, requires 10 GCPs (not recommended in GDAL docs)"
        }
    ]

    def __init__(self,
            epsg_code=None,
            transformation=None
        ):

        self.gcps = []
        self.epsg_code = epsg_code
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
        from osgeo import ogr

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

        valid_ids = [i['id'] for i in self.trans_options]
        if not trans_id in valid_ids:
            k = ", ".join(valid_ids)
            msg = f"invalid transformation identifier must be one of {k}"
            raise TypeError(msg)

        trans = [i for i in self.trans_options if i['id'] == trans_id][0]
        self.transformation = trans

    def set_workspace(self, directory):

        if not os.path.isdir(directory):
            os.mkdir(directory)
        self.workspace = directory

    def get_spatial_reference(self):

        sr = osr.SpatialReference()
        sr.ImportFromEPSG(self.epsg_code)
        return sr

    def georeference_document(self, document, user=None):

        from .models import GCPGroup

        try:
            gcp_group = GCPGroup.objects.get(document=document)
        except GCPGroup.DoesNotExist as e:
            raise e

        if len(self.gcps) == 0:
            self.gcps = gcp_group.gdal_gcps
            self.epsg_code = gcp_group.crs_epsg

        out_path = self.georeference(document.doc_file.path)

        return out_path

    def add_overviews(self, image_path):

        ## add overviews
        ## https://stackoverflow.com/a/61117295/3873885

        Image = gdal.Open(image_path, 1)
        gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
        Image.BuildOverviews("AVERAGE", [2, 4, 8, 16])

    def georeference(self, src_path, output_directory=None, out_format="VRT", addo=False):

        print("start georeferencing")

        if output_directory is None:
            self.set_workspace(os.path.dirname(src_path))
        else:
            self.set_workspace(output_directory)
        
        vrt_with_gcps = get_path_variant(src_path, "gcps", outdir=self.workspace)
        dst_path = get_path_variant(src_path, out_format, outdir=self.workspace)

        # name, ext = os.path.splitext(os.path.basename(src_path))
        # vrt_with_gcps = os.path.join(self.workspace, f"{name}_gcps.vrt")
        # if out_format == "VRT":
            
        # elif out_format == "GTiff":
        #     dst_path = os.path.join(self.workspace, f"{name}_modified.tif")
        # else:
        #     raise Exception("invalid output format")

        print(f"format: {out_format}")

        ## make TranslateOptions object to hold the GCP list and embed that list
        ## into a new image file.
        elapsed = 0
        print("translating...")
        start = time.time()

        to = gdal.TranslateOptions(
            GCPs=self.gcps,
            format="VRT",
        )
        gdal.Translate(vrt_with_gcps, src_path, options=to)

        elapsed += time.time() - start
        print(f"  completed in {time.time() - start} seconds.")

        print("warping...")
        start = time.time()

        sr_wkt = self.get_spatial_reference().ExportToWkt()
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
            format=out_format,
            dstSRS=f"EPSG:{self.epsg_code}",
            dstAlpha=True,

        )
        print(dst_path)

        # with CapturingStderr() as output:
        try:
            print("in try block")
            gdal.UseExceptions()

            f = StringIO()
            with redirect_stderr(f):
                # do_something(my_object)
            
            # with CapturingStdout() as output:
                
                gdal.Warp(dst_path, vrt_with_gcps, options=wo)
                # print(output)
            out = f.getvalue()
            print(out)
        except Exception as e:
            print("exception from warp command")
            print(e)
        # print(output)
        print("warp completed")

        elapsed += time.time() - start
        print(f"  completed in {time.time() - start} seconds.")

        if addo is True:
            print("adding overviews...")
            start = time.time()
            self.add_overviews(dst_path)
            elapsed += time.time() - start
            print(f"  completed in {time.time() - start} seconds.")

        print(f"\nfull process took {elapsed} seconds.")
        return dst_path
