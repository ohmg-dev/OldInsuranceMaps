import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError

from georeference.models.resources import Document, Layer
from georeference.georeferencer import Georeferencer

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=['georeference', 'thumbnail'],
            help="operation to perform",
        )
        parser.add_argument(
            "--docid",
            default=None,
            help="pk for Document resource to be handled.",
        )
        parser.add_argument(
            "--lyrid",
            default=None,
            help="pk for Layer resource to be processed.",
        )
        parser.add_argument(
            "--file",
            default=None,
            help="path for file input (of whatever sort).",
        )
        parser.add_argument(
            "-s",
            "--source",
            default=None,
            help="Path to local file to be georeferenced."
        )
        parser.add_argument(
            "-t",
            "--transformation",
            default=None,
            help="Transformation to use: 'tps' = thin plate spline; "\
                "'poly' = highest possible polynomial based on number of GCPs; "\
                "'poly1' = polynomial 1; "\
                "'poly2' = polynomial 2; "\
                "'poly3' = polynomial 3"
        )
        parser.add_argument(
            "--points-file",
            default=None,
            help="Points file exported from QGIS containing list of GCPs."
        )
        parser.add_argument(
            "--vrt",
            action="store_true",
            default=False,
            help="Uses a VRT during the georeferencing process."
        )

    def handle(self, *args, **options):

        op = options['operation']

        if op == "georeference":
            doc = Document.objects.get(pk=options['docid'])
            print(doc)
            if doc.georeference_sessions.exists():
                list(doc.georeference_sessions)[-1].run()

        elif op == "thumbnail":
            if options['docid']:
                doc = Document.objects.get(pk=options['docid'])
                doc.save(set_thumbnail=True)
            
            elif options['lyrid']:
                lyr = Layer.objects.get(pk=options['lyrid'])
                lyr.save(set_thumbnail=True)
            
            elif options['file']:
                from georeference.renderers import generate_layer_thumbnail_content
                generate_layer_thumbnail_content(options['file'])