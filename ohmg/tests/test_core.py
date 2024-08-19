from pathlib import Path
import filecmp

from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.asgi import ASGIHandler
from django.core.management import call_command
from django.test import tag

from ohmg.core.importers.base import get_importer, SingleFileImporter
from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models import Document

from .base import OHMGTestCase


class BasicTests(OHMGTestCase):

    def test_wsgi(self):
        from ohmg.wsgi import application
        self.assertIsInstance(application, WSGIHandler)

    def test_asgi(self):
        from ohmg.asgi import application
        self.assertIsInstance(application, ASGIHandler)


class ImportersTestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset,
    ]

    def test_single_file_importer(self):
        
        importer = get_importer('single-file')

        self.assertEqual(importer.__class__, SingleFileImporter)


@tag('loc')
class LOCImporterTestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset,
        OHMGTestCase.fixture_sanborn_layerset,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
    ]
    
    def test_loc_importer(self):
        
        importer = get_importer('loc-sanborn')

        identifier = "sanborn03267_002"
        volume = importer.run_import(**{
            'identifier': identifier,
            'locale': "alexandria-la",
            'no-cache': "true",
        })

        self.assertEqual(Volume.objects.filter(pk=volume.pk).count(), 1)

        locale = Place.objects.get(slug="alexandria-la")
        self.assertEqual(locale.volume_count, 1)

    def test_loc_sanborn_jp2_load(self):

        call_command('loaddata', self.fixture_alexandria_volume)

        volume = Volume.objects.get(identifier="sanborn03267_002")

        volume.make_sheets()
        self.assertEqual(len(volume.sheets), 3)

        volume.load_sheet_docs(force_reload=True)

        sheet_p1 = Sheet.objects.get(volume=volume, sheet_no=1)

        self.assertTrue(filecmp.cmp(self.image_alex_p1_original, sheet_p1.doc.file.path, shallow=False))


class MapTestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset,
        OHMGTestCase.fixture_sanborn_layerset,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
    ]

    def test_volume_make_sheets(self):

        call_command('loaddata', self.fixture_alexandria_volume)

        volume = Volume.objects.get(identifier="sanborn03267_002")

        self.assertEqual(Sheet.objects.all().count(), 0)
        volume.make_sheets()

        self.assertEqual(len(volume.sheets), 3)

    def test_volume_load_docs(self):

        call_command('loaddata', self.fixture_alexandria_volume)

        volume = Volume.objects.get(identifier="sanborn03267_002")

        volume.make_sheets()
        self.assertEqual(len(volume.sheets), 3)

        volume.load_sheet_docs()

        sheet_p1 = Sheet.objects.get(volume=volume, sheet_no=1)

        self.assertTrue(filecmp.cmp(self.image_alex_p1_original, sheet_p1.doc.file.path, shallow=False))
