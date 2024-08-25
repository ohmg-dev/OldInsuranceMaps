import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ohmg.tests.base import OHMGTestCase, copy_files_to_media_root
from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models.resources import ItemBase, LayerSet, GCP, GCPGroup, DocumentLink, LayerSetCategory
from ohmg.georeference.models.sessions import SessionBase
from ohmg.places.models import Place
from ohmg.places.management.utils import reset_volume_counts


class Command(BaseCommand):
    help = 'generate various system configuration files that incorporate the '\
           'the current app settings.'
    out_dir = "_system-configs"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            help="Directory containing dumped fixtures."
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete content from database before loading."
        )

    def handle(self, *args, **options):

        def fix_model_name(path, new_name):
            with open(path, "r") as o:
                data = json.load(o)
            for i in data:
                i['model'] = new_name
            new_path = Path(options['source'], path.stem + "-fixed.json")
            with open(new_path, "w") as o:
                json.dump(data, o)
            return new_path

        if options['reset']:
            
            models_to_clear = [
                Sheet,
                Volume,
                ItemBase,
                LayerSet,
                SessionBase,
                GCP,
                GCPGroup,
                Place,
                get_user_model(),
            ]
            for m in models_to_clear:
                m.objects.all().delete()

        fixture_model_lookup = {
            "accounts.user": get_user_model(),
            "georeference.setcategory": LayerSetCategory,
            "places.place": Place,
            "loc_insurancemaps.volume": Volume,
            "loc_insurancemaps.sheet": Sheet,
            "georeference.itembase": ItemBase,
            "georeference.gcpgroup": GCPGroup,
            "georeference.gcp": GCP,
            "georeference.annotationset": LayerSet,
            "georeference.documentlink": DocumentLink,
        }

        for fixture_name in fixture_model_lookup.keys():
            path = Path(options['source'], f"{fixture_name}.json")
            with open(path, "r") as o:
                data = json.load(o)
            
            to_create = []
            for i in data:
                fields = i['fields']
                fields['pk'] = i['pk']
                obj = fixture_model_lookup[fixture_name](**fields)
                to_create.append(obj)
            fixture_model_lookup[fixture_name].objects.bulk_create(to_create)
            # if fixture_name == "georeference.setcategory":
            #     path = fix_model_name(path, "georeference.layersetcategory")
            # if fixture_name == "georeference.annotationset":
            #     path = fix_model_name(path, "georeference.layerset")
            # call_command('loaddata', path)
        