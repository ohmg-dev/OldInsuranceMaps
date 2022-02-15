import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document
from geonode.layers.models import Layer

from georeference.proxy_models import DocumentProxy, LayerProxy
from georeference.models import GCPGroup, GeoreferenceSession

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            default=[
                "retry",
                "revert",
            ],
            help="specify the operation to carry out",
        )
        parser.add_argument(
            "--docid",
            default=None,
            help="pk for GeoNode Document",
        )
        parser.add_argument(
            "--layerid",
            default=None,
            help="alternate for GeoNode Layer",
        )

    def handle(self, *args, **options):

        if options["docid"] is not None:
            dp = DocumentProxy(options["docid"])
        elif options["layerid"] is not None:
            lp = LayerProxy(options["layerid"])
            dp = lp.get_document_proxy()
        else:
            print("must provide docid or layerid (alternate)")
            exit()

        if options["operation"] == "revert":
            dp.revert_georeferencing()
        elif options["operation"] == "retry":
            latest = list(dp.get_georeference_sessions())[-1]
            latest.run()
