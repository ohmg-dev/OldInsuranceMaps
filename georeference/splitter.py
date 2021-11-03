import os
import math
import logging
from PIL import Image, ImageDraw, ImageFilter

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Polygon, LineString

from .utils import make_db_cursor

logger = logging.getLogger(__name__)

class Splitter(object):

    def __init__(self, image_file=None, divisions=[]):

        self.img_file = image_file
        self.divisions = divisions

        if os.path.isdir(settings.TEMP_DIR) is False:
            os.mkdir(settings.TEMP_DIR)
        self.temp_dir = settings.TEMP_DIR

    def make_border_geometry(self, image_file=None):
        """ generates a Polygon from the dimensions of the input image file. """

        if image_file is None:
            image_file = self.img_file

        img = Image.open(image_file)
        w, h = img.size
        coords = [(0,0), (0,h), (w,h), (w,0), (0,0)]

        return Polygon(coords)

    def transform_coordinates(self, shape, img_height):
        """ OpenLayers and PIL use different x,y coordinate systems: in OL 0,0 is
        the bottom left corner, and in PIL 0,0 is the top left corner, so the y
        coordinate must be inverted based on the image's real height. """
        coords = list()
        for coord_pair in shape:
            x, y = coord_pair
            coords.append((x, img_height - y))
        return coords

    def extend_vector(self, p1, p2, distance):
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

    def extend_linestring(self, linestring, distance=10):
        ''' takes the input GEOS LineString and extends it in both directions
        (following the trajectory of each end segment) by the given distance. '''

        coord_list = list(linestring.coords)

        new_start = self.extend_vector(coord_list[1], coord_list[0], distance)
        new_end = self.extend_vector(coord_list[-2], coord_list[-1], distance)

        coord_list.insert(0, new_start)
        coord_list.append(new_end)

        return LineString(coord_list)

    def generate_divisions(self, cutlines):
        """ takes the input border and then tries to cut it with the cutlines.
        any sub polygons resulting from the cut are also compared to the cutlines,
        until all cutlines have been used. """

        initial_geom = self.make_border_geometry(self.img_file)

        ## process input cutlines
        cut_shapes = []
        for l in cutlines:
            ## this function extends each end of the original line by 10 pixels.
            ## this facilitates a more robust splitting process.
            ls_extended = self.extend_linestring(LineString(l))
            cut_shapes.append({"geom": ls_extended, "used": False})

        ## candidates is a list of polygons that may be the final polygons
        ## for the cut process. intially the list only contains the border polygon.
        candidates = [{
            "geom": initial_geom,
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

        self.divisions = out_shapes

        return out_shapes

    def split_image(self, out_format="jpg"):
        """ """

        # update the session info, now that it's about to be run
        print("splitting image...")

        format_lookup = {"jpg": "JPEG", "png": "PNG"}

        img = Image.open(self.img_file)
        w, h = img.size

        out_paths = []
        for n, shape in enumerate(self.divisions, start=1):

            coords = self.transform_coordinates(shape, h)

            # future reference: this is a small rect. in the top left of the image
            # coords = [(0, 100), (50,100), (50, 0), (0, 0)]

            # first generate a mask that will only show the desired content
            shape_mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(shape_mask)
            draw.polygon(coords, fill=255)

            # if the output will have an alpha channel, add a nice lil blur on
            # the edges of the polygon mask
            if out_format == "png":
                shape_mask = shape_mask.filter(ImageFilter.GaussianBlur(2))

            # create a copy of the original image
            cut_image = img.copy()
            
            # apply the polygon mask as an alpha layer, erasing everything else
            cut_image.putalpha(shape_mask)

            # crop the newly cut image down to size
            out_image = cut_image.crop(cut_image.getbbox())

            # if the output should be jpg (RGB), then set all transparent
            # areas to white (255, 255, 255)
            if out_format == "jpg":
                bg = Image.new('RGBA', out_image.size, (255, 255, 255))
                composite = Image.alpha_composite(bg, out_image)
                out_image = composite.convert("RGB")

            # set output file name
            filename = os.path.basename(self.img_file)
            ext = os.path.splitext(filename)[1]
            out_filename = filename.replace(ext, f"__{n}.{out_format}")
            out_path = os.path.join(self.temp_dir, out_filename)

            # finally, save the image out to the specified format
            out_image.save(out_path, format_lookup[out_format])

            out_paths.append(out_path)

        return out_paths
