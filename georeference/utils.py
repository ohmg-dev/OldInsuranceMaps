import os
import string
import random
import logging

from django.conf import settings
from django.urls import reverse

from georeference.georeferencer import get_path_variant

logger = logging.getLogger(__name__)

## ~~ general utils ~~

def full_reverse(view_name, **kwargs):
    """Wraps the reverse utility to prepend the site base domain."""
    base = settings.SITEURL.rstrip("/")
    full_url = base + reverse(view_name, **kwargs)
    return full_url

def slugify(input_string, join_char="-"):

    output = input_string.lower()
    remove_chars = [".", ",", "'", '"', "|", "[", "]", "(", ")"]
    output = "".join([i for i in output if not i in remove_chars])
    for i in ["_", "  ", " - ", " ", "--", "-"]:
        output = output.replace(i, join_char)
    return output.lower()

def analyze_url(request):

    p = request.path

    # really messy parsing to get the layer alternate from the url
    resource_type, res_id = None, None
    if p.startswith("/layers/"):
        resource_type = "layer"
        if not p.startswith("/layers/?") and p != "/layers/":
            spath = request.path.split("/")
            malt = spath[spath.index("layers") + 1]
            try:
                res_id = ":".join([malt.split(":")[-2], malt.split(":")[-1]])
            except IndexError:
                pass

    # slightly cleaner parsing to get the document id from the url
    if request.path.startswith("/documents/"):
        resource_type = "document"
        spath = request.path.split("/")
        maybe_id = spath[spath.index("documents") + 1]
        if maybe_id.isdigit():
            res_id = maybe_id

    return (resource_type, res_id)

def random_alnum(size=6):
    """
    Generate random 6 character alphanumeric string
    credit: https://codereview.stackexchange.com/a/232184
    """
    # List of characters [a-zA-Z0-9]
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(size))
    return code

class MapServerManager(object):
    """Small suite of tools used to manipulate the MapServer mapfile."""

    def __init__(self):

        try:
            self.mapfile = settings.MAPSERVER_MAPFILE
            self.endpoint = settings.MAPSERVER_ENDPOINT
        except AttributeError:
            raise NotImplementedError

    def initialize_mapfile(self):

        file_content = f"""MAP
NAME "Georeference Previews"
STATUS ON
EXTENT -2200000 -712631 3072800 3840000
UNITS METERS

WEB
METADATA
    "wms_title"          "GeoNode Gereferencer Preview Server"  ##required
    "wms_onlineresource" "{self.endpoint}?"   ##required
    "wms_srs"            "EPSG:3857"  ##recommended
    "wms_enable_request" "*"   ##necessary
END
END # Web

PROJECTION
"init=epsg:3857"   ##required
END

#
# Start of layer definitions
#

END # Map File
"""

        with open(self.mapfile, "w") as out:
            out.write(file_content)

        return self.mapfile

    def get_layer_name_from_file(self, file_path):

        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        if layer_name[0].isdigit():
            layer_name = "x" + layer_name
        return layer_name

    def add_layer(self, file_path):

        vrt_path = get_path_variant(file_path, "VRT")

        if not os.path.isfile(self.mapfile):
            self.initialize_mapfile()

        layer_name = self.get_layer_name_from_file(vrt_path)
        output = []
        already_exists = False
        with open(self.mapfile, "r") as openf:

            for line in openf.readlines():
                if line != "END # Map File\n":
                    output.append(line)
                if vrt_path in line:
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
                f'    DATA "{vrt_path}"\n',
                '    OFFSITE 255 255 255\n',
                '    TRANSPARENCY 100\n'
                '    PROJECTION\n',
                '     "init=epsg:3857"\n',
                '    END\n',
                '  END # Layer\n',
                # '\n',
                'END # Map File\n',
            ]
        else:
            output += ['END # Map File\n']

        with open(self.mapfile, "w") as openf:
            openf.writelines(output)
        
        return layer_name

    def remove_layer(self, file_path):

        vrt_path = get_path_variant(file_path, "VRT")

        basename = os.path.basename(vrt_path)
        output = []
        current_layer = {"source": "", "lines": []}
        with open(self.mapfile, "r") as openf:
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

        with open(self.mapfile, "w") as openf:
            openf.writelines(output)
