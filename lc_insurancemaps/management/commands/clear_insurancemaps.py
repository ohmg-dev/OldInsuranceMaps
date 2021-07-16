from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document

from lc_insurancemaps.models import MapScan, MapCollectionItem

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--mapscan",
            action="store_true",
            help="remove all map scans",
        )
        parser.add_argument(
            "--mapcollectionitem",
            action="store_true",
            help="remove all map collection items",
        )
        parser.add_argument(
            "--document",
            action="store_true",
            help="remove all documents",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="removes all map scans, map collection items, and documents",
        )

    def handle(self, *args, **options):

        if options['mapscan']:
            self.delete_mapscans()
        if options['mapcollectionitem']:
            self.delete_collectionitems()
        if options['document']:
            self.delete_documents()
        if options['all']:
            self.delete_documents()
            self.delete_mapscans()
            self.delete_collectionitems()


    def delete_mapscans(self):
        print(f"removing {MapScan.objects.all().count()} MapScan objects")
        MapScan.objects.all().delete()

    def delete_collectionitems(self):
        print(f"removing {MapCollectionItem.objects.all().count()} MapCollectionItem objects")
        MapCollectionItem.objects.all().delete()

    def delete_documents(self):
        print(f"removing {Document.objects.all().count()} Document objects")
        Document.objects.all().delete()
