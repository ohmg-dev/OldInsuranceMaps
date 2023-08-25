import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError

from ohmg.georeference.models.resources import Document, Layer
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.renderers import generate_layer_thumbnail_content

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=['georeference', 'thumbnail', 'set-extent'],
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
            if options['docid']:
                resource = Document.objects.get(pk=options['docid'])
                sessions = resource.georeference_sessions
            elif options['lyrid']:
                resource = Layer.objects.get(pk=options['lyrid'])
                sessions = resource.get_document().georeference_sessions
            print(sessions)
            if sessions.exists():
                list(sessions)[-1].run()

        if op == "set-extent":
            if options['lyrid']:
                lyr = Layer.objects.get(pk=options['lyrid'])
                lyr.save(set_extent=True)

        elif op == "thumbnail":
            if options['docid']:
                doc = Document.objects.get(pk=options['docid'])
                doc.save(set_thumbnail=True)
            
            elif options['lyrid']:
                lyr = Layer.objects.get(pk=options['lyrid'])
                lyr.save(set_thumbnail=True)
            
            elif options['file']:
                content = generate_layer_thumbnail_content(options['file'])
                with open('thumb_output.jpg', 'wb') as out:
                    out.write(content)
