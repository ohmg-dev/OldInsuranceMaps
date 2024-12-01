from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ohmg.tests.base import OHMGTestCase, copy_files_to_media_root
from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models.resources import ItemBase, LayerSet, GCP, GCPGroup
from ohmg.georeference.models.sessions import SessionBase
from ohmg.places.utils import reset_volume_counts


class Command(BaseCommand):
    help = 'generate various system configuration files that incorporate the '\
           'the current app settings.'
    out_dir = "_system-configs"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete content from database before reloading."
        )
        parser.add_argument(
            "--with-prep-sessions",
            action="store_true",
            help="Include some complete prep sessions in the pre-populated data."
        )
        parser.add_argument(
            "--with-georef-sessions",
            action="store_true",
            help="Include some complete georef sessions in the pre-populated data."
        )

    def handle(self, *args, **options):

        if options['reset']:
            
            models_to_clear = [
                Sheet,
                Volume,
                ItemBase,
                LayerSet,
                SessionBase,
                GCP,
                GCPGroup,
                get_user_model(),
            ]
            for m in models_to_clear:
                m.objects.all().delete()

        for fixture in [
            OHMGTestCase.fixture_admin_user,
            OHMGTestCase.fixture_default_layerset_categories,
            OHMGTestCase.fixture_sanborn_layerset_categories,
            OHMGTestCase.fixture_alexandria_place,
            OHMGTestCase.fixture_alexandria_volume,
            OHMGTestCase.fixture_alexandria_main_layerset,
            OHMGTestCase.fixture_alexandria_docs,
            OHMGTestCase.fixture_alexandria_sheets,
        ]:
            call_command('loaddata', fixture)
        
        ## copy files from test data to media folder
        copy_files_to_media_root([
            OHMGTestCase.image_alex_p1_original,
            OHMGTestCase.image_alex_p2_original,
            OHMGTestCase.image_alex_p3_original,
        ], "documents")

        ## copy all thummbnails now...
        copy_files_to_media_root(OHMGTestCase.thumbnail_dir.glob("*"), "thumbnails")

        if options['with_prep_sessions'] or options['with_georef_sessions']:
            
            for fixture in [
                OHMGTestCase.fixture_session_prep_no_split,
                OHMGTestCase.fixture_session_prep_split,
                OHMGTestCase.fixture_document_split_results,
                OHMGTestCase.fixture_document_links_split,
            ]:
                call_command('loaddata', fixture)

            copy_files_to_media_root([
                OHMGTestCase.image_alex_p2__1,
                OHMGTestCase.image_alex_p2__2,
            ], "documents")

            # some manual modifications to the items to reflect the session changes
            doc_p2 = ItemBase.objects.get(pk=2)
            doc_p2.set_status("split")
            doc_p3 = ItemBase.objects.get(pk=3)
            doc_p3.set_status("prepared")

        if options['with_georef_sessions']:
            
            for fixture in [
                OHMGTestCase.fixture_document_georef_results_lyr,
                OHMGTestCase.fixture_document_georef_results_gcpgroup,
                OHMGTestCase.fixture_document_georef_results_gcps,
                OHMGTestCase.fixture_session_georef,
                OHMGTestCase.fixture_document_links_georef,
            ]:
                call_command('loaddata', fixture)

            copy_files_to_media_root([OHMGTestCase.image_alex_p2__2_lyr], "layers")
            
            # some manual modifications to the items to reflect the session changes
            doc_p2_2 = ItemBase.objects.get(pk=5)
            doc_p2_2.set_status("georeferenced")
            lyr_p2_2 = ItemBase.objects.get(pk=6)
            lyr_p2_2.set_status("georeferenced")

        reset_volume_counts()
        for v in Volume.objects.all():
            v.update_status("ready")
            v.refresh_lookups()
