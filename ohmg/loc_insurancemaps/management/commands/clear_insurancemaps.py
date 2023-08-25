from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map

from ohmg.loc_insurancemaps.models import Volume, Sheet, FullThumbnail

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
            delete_list = [Document]
        if options['all']:
            delete_list = [
                Document,
                Layer,
                Volume,
                Sheet,
                Map,
                FullThumbnail,
            ]
        
        for model in delete_list:
            objs = model.objects.all()
            print(f"removing {objs.count()} {model.__name__} objects")
            objs.delete()
