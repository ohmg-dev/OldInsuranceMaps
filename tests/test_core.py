from pathlib import Path
import filecmp

from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.asgi import ASGIHandler
from django.test import tag, Client

from ohmg.core.importers.base import get_importer
from ohmg.core.importers.single_file import SingleFileImporter
from ohmg.core.models import (
    Map,
    Document,
    Region,
    Layer,
)
from ohmg.places.models import Place
from ohmg.georeference.models import PrepSession, GeorefSession

from .base import OHMGTestCase


class BasicTests(OHMGTestCase):
    def test_wsgi(self):
        from ohmg.wsgi import application

        self.assertIsInstance(application, WSGIHandler)

    def test_asgi(self):
        from ohmg.asgi import application

        self.assertIsInstance(application, ASGIHandler)

    def test_sitemap(self):
        response = Client().get("/sitemap.xml/")
        self.assertEqual(response.status_code, 200)


class ImportersTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
    ]

    def test_single_file_importer(self):
        importer = get_importer("single-file")

        self.assertEqual(importer.__class__, SingleFileImporter)


@tag("loc")
class LOCImporterTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
    ]

    def test_loc_importer(self):
        importer = get_importer("loc-sanborn")

        identifier = "sanborn03267_002"
        map = importer.run_import(
            **{
                "identifier": identifier,
                "locale": "alexandria-la",
                "no-cache": "true",
            }
        )

        self.assertEqual(Map.objects.filter(pk=map.pk).count(), 1)
        self.assertEqual(len(map.document_sources), 3)

        locale = Place.objects.get(slug="alexandria-la")
        self.assertEqual(locale.volume_count, 1)

        map.create_documents(get_files=True)

        doc_p1 = Document.objects.get(map=map, page_number=1)

        self.assertTrue(filecmp.cmp(self.image_alex_p1_original, doc_p1.file.path, shallow=False))


class MapTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_map,
    ]

    def test_create_documents(self):
        map = Map.objects.get(identifier="sanborn03267_002")

        self.assertEqual(Document.objects.all().count(), 0)
        map.create_documents()

        self.assertEqual(len(map.documents.all()), 3)


@tag("sessions")
class PreparationSessionTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_map,
        OHMGTestCase.fixture_alexandria_docs,
    ]

    def test_prepsession_no_split(self):
        document = Document.objects.get(pk=3)
        user = get_user_model().objects.get(username="admin")

        session = PrepSession.objects.create(
            doc2=document,
            user=user,
        )
        session.data["split_needed"] = False
        session.save(update_fields=["data"])
        session.run()

        self.assertTrue(document.prepared)

        region = Region.objects.filter(document=document)
        self.assertEqual(region.count(), 1)

    def test_prepsession_split(self):
        document = Document.objects.get(pk=2)
        user = get_user_model().objects.get(username="admin")

        cutlines = [[[2507.8125, 7650], [2522.75390625, 0]]]

        session = PrepSession.objects.create(
            doc2=document,
            user=user,
        )

        session.data["split_needed"] = True
        session.data["cutlines"] = cutlines

        session.save(update_fields=["data"])
        session.run()

        self.assertTrue(document.prepared)

        regions = Region.objects.filter(document=document)
        self.assertEqual(regions.count(), 2)

        for region in regions:
            file_path = Path(region.file.path)
            control_file_path = self.DATA_DIR / "files/split_images" / file_path.name

            self.assertTrue(filecmp.cmp(control_file_path, file_path, shallow=False))


@tag("sessions")
class GeoreferenceSessionTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_map,
        OHMGTestCase.fixture_alexandria_docs,
        OHMGTestCase.fixture_session_prep_no_split,
        OHMGTestCase.fixture_session_prep_split,
        OHMGTestCase.fixture_alexandria_regs,
    ]

    def test_georef_session(self):
        region = Region.objects.get(pk=3)
        user = get_user_model().objects.get(username="admin")

        session = GeorefSession.objects.create(
            reg2=region,
            user=user,
        )

        input_gcp_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-92.44538695899614, 31.312902143444333],
                    },
                    "properties": {
                        "id": "1d613210-4114-4b58-8d28-839b26867c68",
                        "note": "",
                        "image": [3547, 3173],
                        "listId": 1,
                        "username": "admin",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-92.44657641570406, 31.311858470117244],
                    },
                    "properties": {
                        "id": "80a64c7f-85e6-40f8-bc29-5709681e03d8",
                        "note": "",
                        "image": [3564, 6276],
                        "listId": 2,
                        "username": "admin",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-92.44718721779732, 31.312339110585995],
                    },
                    "properties": {
                        "id": "fab611f5-cf0d-4409-81a2-ebb59b7acfba",
                        "note": "",
                        "image": [2004, 6243],
                        "listId": 3,
                        "username": "admin",
                    },
                },
            ],
        }
        session.data["epsg"] = 3857
        session.data["gcps"] = input_gcp_geojson
        session.data["transformation"] = "poly1"
        session.save(update_fields=["data"])
        session.run()

        self.assertTrue(region.georeferenced)

        layers = Layer.objects.filter(region=region)
        self.assertEqual(layers.count(), 1)
        layer = layers[0]

        self.assertTrue(filecmp.cmp(self.image_alex_p2__2_lyr, layer.file.path, shallow=False))

        self.assertIsNotNone(region.gcp_group)
        self.assertEqual(len(region.gcp_group.gcps), 3)

        # need to delete listId before comparison as it is not returned by as_geojson
        for i in input_gcp_geojson["features"]:
            del i["properties"]["listId"]
        self.assertEqual(region.gcp_group.as_geojson, input_gcp_geojson)

        # import sys
        # from django.core.management import call_command
        # sysout = sys.stdout
        # sys.stdout = open('filename.json', 'w')
        # call_command("dumpdata", "core.Layer", "--indent=2")
        # sys.stdout = sysout
