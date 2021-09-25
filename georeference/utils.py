import os
import math
import json
import base64
import logging
import psycopg2
import urllib.request
from PIL import Image
from osgeo import gdal, osr

from django.conf import settings
from django.core.files import File
from django.contrib.gis.geos import GEOSGeometry, Polygon, LineString
from django.urls import reverse

from .models import GCP

logger = logging.getLogger(__name__)

def make_db_cursor():

    ## make connection to postgis database
    db = settings.DATABASES['default']
    db_conn = "dbname = {} port = {} user = {} host = {} password = {}".format(
        db['NAME'],db['PORT'],db['USER'],db['HOST'],db['PASSWORD'])
    conn = psycopg2.connect(db_conn)

    return conn.cursor()

def make_border_geometery(image_file):
    """ generates a Polygon from the dimensions of the input image file. """

    img = Image.open(image_file)
    w, h = img.size
    coords = [(0,0), (0,h), (w,h), (w,0), (0,0)]

    return Polygon(coords)

def extend_linestring(linestring, distance=10):
    ''' takes the input GEOS LineString and extends it in both directions
    (following the trajectory of each end segment) by the given distance. '''

    coord_list = list(linestring.coords)

    new_start = extend_vector(coord_list[1], coord_list[0], distance)
    new_end = extend_vector(coord_list[-2], coord_list[-1], distance)

    coord_list.insert(0, new_start)
    coord_list.append(new_end)

    return LineString(coord_list)

def extend_vector(p1, p2, distance):
    '''https://math.stackexchange.com/a/3346108 (credit to Oliver Roche)
    takes the two input points, which represent a vector, and creates a
    third point that would extend that vector by the given distance.'''

    x1, y1 = p1
    x2, y2 = p2
    rise = y2 - y1
    run = x2 - x1

    norm = math.sqrt((run ** 2) + (rise ** 2))

    # if negative coords are used norm will be 0.0, silently return original point
    if norm == 0.0:
        return (x2, y2)

    x3 = x2 + distance * (run/norm)
    y3 = y2 + distance * (rise/norm)

    return (x3, y3)

def transform_coordinates(shape, img_height):
    """ OpenLayers and PIL use different x,y coordinate systems: in OL 0,0 is
    the bottom left corner, and in PIL 0,0 is the top left corner, so the y
    coordinate must be inverted based on the image's real height. """
    coords = list()
    for coord_pair in shape:
        x, y = coord_pair
        coords.append((x, img_height - y))
    return coords

def cut_geometry_by_lines(border, cutlines):
    """ takes the input border and then tries to cut it with the cutlines.
    any sub polygons resulting from the cut are also compared to the cutlines,
    until all cutlines have been used. """

    ## process input cutlines
    cut_shapes = []
    for l in cutlines:
        ## this function extends each end of the original line by 10 pixels.
        ## this facilitates a more robust splitting process.
        ls_extended = extend_linestring(LineString(l))
        cut_shapes.append({"geom": ls_extended, "used": False})

    ## candidates is a list of polygons that may be the final polygons
    ## for the cut process. intially the list only contains the border polygon.
    candidates = [{
        "geom": border,
        "evaluated": False,
        "final": True
    }]

    cursor = make_db_cursor()

    while True:
        ## evaluate one clipped shape at a time.
        for candidate in [i for i in candidates if not i["evaluated"]]:
            candidate["evaluated"] = True

            ## iterate all of the clip lines to try against this one shape.
            ## exclude those that have already been used to cut a shape.
            for cut in [i for i in cut_shapes if not i["used"]]:

                ## quick skip this cutline if it doesn't even touch the
                ## polygon that is being evaluated.
                if not candidate["geom"].intersects(cut["geom"]):
                    continue

                sql = f'''
SELECT ST_AsText((ST_Dump(ST_Split(border, cut))).geom) AS wkt
FROM (SELECT
 ST_SnapToGrid(ST_GeomFromText(' {candidate["geom"].wkt} '), 1) AS border,
 ST_SnapToGrid(ST_GeomFromText(' {cut["geom"].wkt} '), 1) AS cut) AS foo;
                '''
                cursor.execute(sql)
                rows = cursor.fetchall()

                ## if only one row is returned it means that the line was
                ## insufficient to cut the polygon. This check is likely
                ## redundant at this point in the process though.
                if len(rows) > 1:

                    ## if a proper cut has been made, this cutline should be
                    ## ignored on future iterations.
                    cut['used'] = True

                    ## if this candidate has been split, it will not be one
                    ## of the final polygons.
                    candidate["final"] = False

                    ## turn each of the resulting polygons from the cut into
                    ## new candidates for future iterations.
                    for row in rows:
                        geom = GEOSGeometry(row[0])
                        candidates.append({
                            "geom": geom,
                            "evaluated": False,
                            "final": True
                        })
                    break

        ## break the while loop once all of the candidates have been evaluated
        if all([i["evaluated"] for i in candidates]):
            break

    out_shapes = [i["geom"].coords[0] for i in candidates if i["final"] is True]

    print(f"{len(out_shapes)} output shapes")
    return out_shapes


## ~~ IIIF support ~~

def document_as_iiif_resource(document, iiif_server=False):

    img = Image.open(document.doc_file)
    width, height = img.size

    resource = {
      "@type": "dctypes:Image",
      "width": width,
      "height": height
    }

    if iiif_server is True:
        iiif2_base = f"{settings.IIIF_SERVER_LOCATION}/iiif/2"
        fname = os.path.basename(document.doc_file.name)
        resource["@id"] = f"{iiif2_base}/{fname}/full/max/0/default.jpg",
        resource["service"] = {
            "@context": "http://iiif.io/api/image/2/context.json",
            "@id": f"{iiif2_base}/{fname}",
            "profile": "http://iiif.io/api/image/2/level2.json",
            "protocol": "http://iiif.io/api/image"
        }
    else:
        img_url = settings.SITEURL.rstrip("/") + document.doc_file.url
        resource["@id"] = img_url

    return resource

def document_as_iiif_canvas(document, resource=None, iiif_server=False):

    this_url = reverse('document_canvas', args=(document.id,))
    canvas_id = settings.SITEURL.rstrip("/") + this_url

    if resource is None:
        resource = document_as_iiif_resource(document, iiif_server=iiif_server)

    canvas = {
      "@context": "http://iiif.io/api/presentation/2/context.json",
      "@id": canvas_id,
      "@type": "sc:Canvas",
      "label": "CanvasLabel",
      "width": resource["width"],
      "height": resource["height"],
      "images": [
        {
          "@type": "oa:Annotation",
          "motivation": "sc:painting",
          "on": canvas_id,
          "resource": resource
        }
      ]
    }

    return canvas

def document_as_iiif_manifest(document, canvas=None, iiif_server=False):
    """ creates a manifest for the document's image """

    # this base64 encoding seems optional, but would probably be good to work in
    base_url = "http://localhost:8080/cantaloupe/iiii/2/"
    urlSafeEncodedBytes = base64.urlsafe_b64encode(base_url.encode("utf-8"))
    urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")

    this_url = reverse('document_manifest', args=(document.id,))
    manifest_id = settings.SITEURL.rstrip("/") + this_url

    if canvas is None:
        canvas = document_as_iiif_canvas(document, iiif_server=iiif_server)

    manifest = {
      "@context": "http://iiif.io/api/presentation/2/context.json",
      "@type": "sc:Manifest",
      "@id": manifest_id,
      "label": document.title,
      "description": "Description.",
      "attribution": "Attribution",
      "thumbnail": document.thumbnail_url,
      "sequences": [
        {
          "@type": "sc:Sequence",
          "canvases": [
            canvas
          ]
        }
      ]
    }

    return manifest

## ~~ Geoserver VRT utilities ~~
from geonode.geoserver.helpers import OGC_Servers_Handler
from geoserver.catalog import Catalog

def get_gs_catalog():
    """create the GeoServer catalog object"""

    ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

    _user, _password = ogc_server_settings.credentials

    url = ogc_server_settings.rest
    gs_catalog = Catalog(url, _user, _password,
                        retries=ogc_server_settings.MAX_RETRIES,
                        backoff_factor=ogc_server_settings.BACKOFF_FACTOR)

    return gs_catalog

def get_gs_layer_from_document(document, workspace="geonode"):

    cat = get_gs_catalog()
    doc_path = document.doc_file.path
    gs_layer_name = os.path.splitext(os.path.basename(doc_path))[0]
    gs_layer = cat.get_layer(gs_layer_name)

    return gs_layer

def create_layer_from_vrt(vrt_path, workspace="geonode"):

    cat = get_gs_catalog()
    cat._cache.clear()
    name = os.path.splitext(os.path.basename(vrt_path))[0]
    store_names = [i.name for i in cat.get_stores()]
    print(name)
    print(store_names)
    if name not in store_names:
        print("creating new store/layer")
        store = cat.create_coveragestore(name,
            path=vrt_path,
            workspace=workspace,
            type="VRT",
            overwrite=True,
            # create_layer=False
        )
        print("complete")
    else:
        store = cat.get_stores(names=name, workspaces=[workspace])[0]
    print(store)
    print(store.href)


    gs_layer = cat.get_layer(name)
    print(gs_layer)

    return {
        "name": name,
        "layer": gs_layer,
        "workspace_name": workspace,
        "store": store,
    }

## ~~ Mapserver layer manipulation functions ~~

def mapserver_add_layer(file_path):

    mapfile = settings.MAPSERVER_MAPFILE

    layer_name = os.path.splitext(os.path.basename(file_path))[0]
    output = []
    already_exists = False
    with open(mapfile, "r") as openf:

        for line in openf.readlines():
            if line != "END # Map File\n":
                output.append(line)
            if file_path in line:
                already_exists = True
    
    if not already_exists:
        output += [
            '  LAYER\n',
            f'    NAME "{layer_name}"\n',
            '    METADATA\n',
            f'      "wms_title" "{layer_name}"\n',
            '    END\n',
            '    TYPE RASTER\n',
            '    STATUS ON\n',
            f'    DATA "{file_path}"\n',
            '    PROJECTION\n',
            '     "init=epsg:3857"\n',
            '    END\n',
            '  END # Layer\n',
            # '\n',
            'END # Map File\n',
        ]
    else:
        output += ['END # Map File\n']

    with open(mapfile, "w") as openf:
        openf.writelines(output)
    
    return layer_name

def mapserver_remove_layer(file_path):

    mapfile = settings.MAPSERVER_MAPFILE

    basename = os.path.basename(file_path)
    output = []
    current_layer = {"source": "", "lines": []}
    with open(mapfile, "r") as openf:
        in_layer = False
        skip_layer = False
        for line in openf.readlines():

            if line == "  LAYER\n":
                in_layer = True
            
            if not in_layer:
                output.append(line)
            
            if in_layer is True:
                current_layer['lines'].append(line)

            if basename in line:
                skip_layer = True

            if line == "  END # Layer\n":
                in_layer = False
                if skip_layer is False:
                    output += current_layer['lines']
                current_layer['lines'] = []
    
    with open(mapfile, "w") as openf:
        openf.writelines(output)
