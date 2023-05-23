from django.core.management.base import BaseCommand, CommandError

from georeference.mosaicker import make_geotiff, make_mosaicjson

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "identifier",
            help="Identifer of item to be mosaicked.",
        )
        parser.add_argument(
            "-f", "--format",
            choices=["geotiff", "mosaicjson"],
            help="Output format",
        )
        parser.add_argument(
            "--trim-all",
            action="store_true",
            default=False,
            help="Output format",
        )

    def handle(self, *args, **options):
        print(options)
        if options['format'] == "mosaicjson":
            make_mosaicjson(options['identifier'], trim_all=options['trim_all'])
        elif options['format'] == "geotiff":
            make_geotiff(options['identifier'], trim_all=options['trim_all'])
        else:
            print("--format must be geotiff or mosaicjson")