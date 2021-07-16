from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document

from georeference.models import SplitSession, SplitLink

class Command(BaseCommand):
    help = 'management commands for mapserver integration'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["mapfile", "apache"],
            help="creates a fresh mapfile mapserver.map at the location "\
                "specified by settings.MAPSERVER_MAPFILE",
        )
        parser.add_argument(
            "--mapserver-bin",
            help="path to mapserver binary needed for nginx config",
        )

    def handle(self, *args, **options):

        if options["operation"] == "mapfile":
            self.create_mapfile()

        if options["operation"] == "apache":
            pass
            # if not options["mapserver-bin"]:
            #     print("no --mapserver-bin provided")
            #     exit()

            # self.create_nginx_config(options['mapserver-bin'])

    def write_file(self, file_path, content):

        with open(file_path, "w") as out:
            out.write(content)
        return file_path

    def create_mapfile(self):

        file_content = f"""MAP
  NAME "Georeference Previews"
  STATUS ON
  EXTENT -2200000 -712631 3072800 3840000
  UNITS METERS

  WEB
    METADATA
      "wms_title"          "GeoNode Gereferencer Preview Server"  ##required
      "wms_onlineresource" "{settings.MAPSERVER_ENDPOINT}?"   ##required
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

        self.write_file(settings.MAPSERVER_MAPFILE, file_content)
