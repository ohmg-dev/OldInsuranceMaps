from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.asgi import ASGIHandler

from ohmg.core.importers.base import get_importer, SingleFileImporter
from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models import Document

from .base import OHMGTestCase, TEST_DATA_DIR


class BasicTests(OHMGTestCase):

    def test_wsgi(self):
        from ohmg.wsgi import application
        self.assertIsInstance(application, WSGIHandler)

    def test_asgi(self):
        from ohmg.asgi import application
        self.assertIsInstance(application, ASGIHandler)


class ImportersTestCase(OHMGTestCase):

    fixtures = [
        'ohmg/georeference/fixtures/default-layerset-categories.json',
        'ohmg/georeference/fixtures/sanborn-layerset-categories.json',
        TEST_DATA_DIR / 'fixtures/places/alexandria-la-and-parents.json',
    ]

    def test_single_file_importer(self):
        
        importer = get_importer('single-file')

        self.assertEqual(importer.__class__, SingleFileImporter)

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

class MapTestCase(OHMGTestCase):

    fixtures = [
        'ohmg/georeference/fixtures/default-layerset-categories.json',
        'ohmg/georeference/fixtures/sanborn-layerset-categories.json',
        TEST_DATA_DIR / 'fixtures/places/alexandria-la-and-parents.json',
        TEST_DATA_DIR / 'fixtures/auth/admin-user.json',
        TEST_DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-volume.json',
        TEST_DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-docs.json',
        TEST_DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-sheets.json',
    ]

    def test_volume_operations(self):

        self.assertEqual(Volume.objects.all().count(), 1)
        self.assertEqual(Sheet.objects.all().count(), 3)
        self.assertEqual(Document.objects.all().count(), 3)
