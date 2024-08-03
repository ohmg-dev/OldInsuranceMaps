from pathlib import Path

from django.test import TestCase
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.asgi import ASGIHandler

from ohmg.core.importers.base import get_importer, SingleFileImporter
from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume

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
        'ohmg/tests/fixtures/places/alexandria-la-tree.json',
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
