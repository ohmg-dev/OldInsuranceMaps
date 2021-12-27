from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from georeference.utils import MapServerManager

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
            help="path to mapserver binary needed for apache site conf",
        )

    def handle(self, *args, **options):

        ms = MapServerManager()

        if options["operation"] == "mapfile":
            ms.initialize_mapfile()

        if options["operation"] == "apache":
            pass
            # if not options["mapserver-bin"]:
            #     print("no --mapserver-bin provided")
            #     exit()

            # self.create_nginx_config(options['mapserver-bin'])
