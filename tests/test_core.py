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
    LayerSet,
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
        OHMGTestCase.Fixtures.region_categories,
        OHMGTestCase.Fixtures.layerset_categories,
    ]

    def test_single_file_importer(self):
        importer = get_importer("single-file")

        self.assertEqual(importer.__class__, SingleFileImporter)


@tag("loc")
class LOCImporterTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.Fixtures.region_categories,
        OHMGTestCase.Fixtures.region_categories_sanborn,
        OHMGTestCase.Fixtures.layerset_categories,
        OHMGTestCase.Fixtures.layerset_categories_sanborn,
        OHMGTestCase.Fixtures.admin_user,
        OHMGTestCase.Fixtures.new_iberia_place,
    ]

    def test_loc_importer(self):
        importer = get_importer("loc-sanborn")

        identifier = "sanborn03375_001"
        map = importer.run_import(
            **{
                "identifier": identifier,
                "locale": "new-iberia-la",
                "no-cache": "true",
            }
        )

        self.assertEqual(Map.objects.filter(pk=map.pk).count(), 1)
        self.assertEqual(len(map.document_sources), 3)

        locale = Place.objects.get(slug="new-iberia-la")
        self.assertEqual(locale.volume_count, 1)

        map.create_documents()
        map.load_all_document_files("admin")

        doc_p1 = Document.objects.get(map=map, page_number=1)

        self.assertTrue(
            filecmp.cmp(self.Files.new_iberia_p1_original, doc_p1.file.path, shallow=False)
        )


class MapTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.Fixtures.region_categories,
        OHMGTestCase.Fixtures.region_categories_sanborn,
        OHMGTestCase.Fixtures.layerset_categories,
        OHMGTestCase.Fixtures.layerset_categories_sanborn,
        OHMGTestCase.Fixtures.admin_user,
        OHMGTestCase.Fixtures.new_iberia_place,
        OHMGTestCase.Fixtures.new_iberia_map,
    ]

    def test_create_documents(self):
        map = Map.objects.get(identifier="sanborn03375_001")

        self.assertEqual(Document.objects.all().count(), 0)
        map.create_documents()

        self.assertEqual(len(map.documents.all()), 3)


@tag("sessions")
class PreparationSessionTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.Fixtures.region_categories,
        OHMGTestCase.Fixtures.region_categories_sanborn,
        OHMGTestCase.Fixtures.layerset_categories,
        OHMGTestCase.Fixtures.layerset_categories_sanborn,
        OHMGTestCase.Fixtures.admin_user,
        OHMGTestCase.Fixtures.new_iberia_place,
        OHMGTestCase.Fixtures.new_iberia_map,
        OHMGTestCase.Fixtures.new_iberia_docs,
    ]

    def test_prepsession_split(self):
        document = Document.objects.get(pk=1)
        user = get_user_model().objects.get(username="admin")

        cutlines = [
            [
                [6450, 5627.483165856904],
                [5284.7586517694235, 5597.601228404641],
                [5332.569751693044, 2442.0686334457364],
                [6450, 2442.068633445737],
            ],
            [
                [5332.569751693044, 2442.0686334457364],
                [3557.5826670286597, 2442.0686334457364],
                [4366.846593904307, -110.92198113880431],
            ],
        ]

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
        self.assertEqual(regions.count(), 3)

        for region in regions:
            file_path = Path(region.file.path)
            control_file_path = self.DATA_DIR / "files/regions" / file_path.name

            self.assertTrue(filecmp.cmp(control_file_path, file_path, shallow=False))

    def test_prepsession_no_split(self):
        document = Document.objects.get(pk=2)
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


@tag("sessions")
class GeoreferenceSessionTestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.Fixtures.region_categories,
        OHMGTestCase.Fixtures.region_categories_sanborn,
        OHMGTestCase.Fixtures.layerset_categories,
        OHMGTestCase.Fixtures.layerset_categories_sanborn,
        OHMGTestCase.Fixtures.admin_user,
        OHMGTestCase.Fixtures.new_iberia_place,
        OHMGTestCase.Fixtures.new_iberia_map,
        OHMGTestCase.Fixtures.new_iberia_docs,
        OHMGTestCase.Fixtures.prepsession_new_iberia_p1_split,
        OHMGTestCase.Fixtures.new_iberia_reg_1__1,
        OHMGTestCase.Fixtures.new_iberia_reg_1__2,
        OHMGTestCase.Fixtures.new_iberia_reg_1__3,
        OHMGTestCase.Fixtures.prepsession_new_iberia_p2_no_split,
        OHMGTestCase.Fixtures.new_iberia_reg_2,
    ]

    def test_georef_session(self):
        region = Region.objects.get(pk=2)
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
                        "coordinates": [-91.82465678442605, 30.010823076580564],
                    },
                    "properties": {
                        "id": "395fb4f8-eebc-4acb-94ff-8875e534fcbe",
                        "note": "",
                        "image": [317, 420],
                        "listId": 1,
                        "username": "admin",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-91.81695598033974, 30.00258275089672],
                    },
                    "properties": {
                        "id": "66809cb3-d7ac-4743-9ff1-e844342a2975",
                        "note": "",
                        "image": [363, 2765],
                        "listId": 2,
                        "username": "admin",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-91.81834687446985, 30.005931842820672],
                    },
                    "properties": {
                        "id": "0bdb4504-d5d9-4f62-9846-313abf1196c8",
                        "note": "",
                        "image": [608, 2012],
                        "listId": 3,
                        "username": "admin",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-91.82244394175576, 30.01248456544343],
                    },
                    "properties": {
                        "id": "f781ccf3-7f9e-4c44-a9c2-ef33de528c7e",
                        "note": "",
                        "image": [871, 404],
                        "listId": 4,
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

        self.assertEqual(LayerSet.objects.all().count(), 1)
        self.assertEqual(LayerSet.objects.all()[0], layer.layerset2)

        self.assertTrue(
            filecmp.cmp(self.Files.new_iberia_p1__1_lyr, layer.file.path, shallow=False)
        )

        self.assertTrue(hasattr(region, "gcpgroup"))
        self.assertEqual(len(region.gcpgroup.gcps), 4)

        # need to delete listId before comparison as it is not returned by as_geojson
        for i in input_gcp_geojson["features"]:
            del i["properties"]["listId"]
        self.assertEqual(region.gcpgroup.as_geojson, input_gcp_geojson)
