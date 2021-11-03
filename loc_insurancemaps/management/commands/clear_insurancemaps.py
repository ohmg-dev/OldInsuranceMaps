from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document
from geonode.maps.models import Map

from loc_insurancemaps.models import Volume, Sheet, FullThumbnail

class Command(BaseCommand):
    help = 'delete model instances.'

    def add_arguments(self, parser):
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

        if options['document']:
            self.delete_documents()
        if options['all']:
            self.delete_documents()
            self.delete_volumes()
            self.delete_sheets()
            self.delete_maps()
            self.delete_thumbs()

    def delete_documents(self):
        print(f"removing {Document.objects.all().count()} Document objects")
        Document.objects.all().delete()
    
    def delete_volumes(self):
        print(f"removing {Volume.objects.all().count()} Volume objects")
        Volume.objects.all().delete()
    
    def delete_sheets(self):
        print(f"removing {Sheet.objects.all().count()} Sheet objects")
        Sheet.objects.all().delete()

    def delete_maps(self):
        print(f"removing {Map.objects.all().count()} Map objects")
        Map.objects.all().delete()

    def delete_thumbs(self):
        print(f"removing {FullThumbnail.objects.all().count()} FullThumbnail objects")
        FullThumbnail.objects.all().delete()
