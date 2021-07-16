import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document

from georeference.models import GCPGroup
from georeference.georeferencer import georeference_document, Georeferencer

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        parser.add_argument(
            "--docid",
            default=None,
            help="pk for GeoNode Document to be georeferenced.",
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

        g = Georeferencer(epsg_code=3857)

        if options["points_file"] is not None:
            g.load_gcps_from_file(options["points_file"])

        if options["transformation"] is not None:
            g.set_transformation(options["transformation"])

        if options["source"] is not None:
            g.georeference(options["source"], vrt=options["vrt"])
            # if options["vrt"] is True:
            #     g.georeference_vrt(options["source"], addo=True)
            # else:
            #     g.georeference(options["source"], addo=True)

        # doc = Document.objects.get(id=options['docid'])
        #
        # output = georeference_document(doc, transformation=options['transformation'])
        # print(output)
