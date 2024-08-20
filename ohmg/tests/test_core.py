from pathlib import Path
import filecmp

from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.asgi import ASGIHandler
from django.core.management import call_command
from django.test import tag

from ohmg.core.importers.base import get_importer, SingleFileImporter
from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models import Document, PrepSession, GeorefSession, DocumentLink

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
        OHMGTestCase.fixture_default_layerset_categories,
    ]

    def test_single_file_importer(self):
        
        importer = get_importer('single-file')

        self.assertEqual(importer.__class__, SingleFileImporter)


@tag('loc')
class LOCImporterTestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
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
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_volume,
    ]

    def test_volume_make_sheets(self):

        volume = Volume.objects.get(identifier="sanborn03267_002")

        self.assertEqual(Sheet.objects.all().count(), 0)
        volume.make_sheets()

        self.assertEqual(len(volume.sheets), 3)

    def test_volume_load_docs(self):

        volume = Volume.objects.get(identifier="sanborn03267_002")

        volume.make_sheets()
        self.assertEqual(len(volume.sheets), 3)

        volume.load_sheet_docs()

        sheet_p1 = Sheet.objects.get(volume=volume, sheet_no=1)

        self.assertTrue(filecmp.cmp(self.image_alex_p1_original, sheet_p1.doc.file.path, shallow=False))


@tag('sessions')
class PreparationSessionTestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_volume,
        OHMGTestCase.fixture_alexandria_docs,
        OHMGTestCase.fixture_alexandria_sheets,
    ]

    def test_prepsession_no_split(self):

        document = Document.objects.get(pk=3)
        user = get_user_model().objects.get(username="admin")

        session = PrepSession.objects.create(
            doc=document,
            user=user,
        )
        session.data['split_needed'] = False
        session.save(update_fields=["data"])
        session.run()

        self.assertEqual(document.status, "prepared")

    def test_prepsession_split(self):

        document = Document.objects.get(pk=2)
        user = get_user_model().objects.get(username="admin")

        cutlines = [[[2507.8125, 7650], [2522.75390625, 0]]]

        session = PrepSession.objects.create(
            doc=document,
            user=user,
        )

        session.data['split_needed'] = True
        session.data['cutlines'] = cutlines

        session.save(update_fields=["data"])
        session.run()

        self.assertEqual(document.status, "split")
        self.assertEqual(DocumentLink.objects.filter(link_type="split", source=document).count(), 2)

        # need to delete this cached_property so it is properly recalculated
        del document.children
        children = document.children
        self.assertEqual(len(children), 2)

        for child in children:
            file_path = Path(child.file.path)
            control_file_path = self.DATA_DIR / "files/split_images" / file_path.name

            self.assertTrue(filecmp.cmp(control_file_path, file_path, shallow=False))


@tag('sessions')
class GeoreferenceSessionTestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_volume,
        OHMGTestCase.fixture_alexandria_docs,
        OHMGTestCase.fixture_alexandria_sheets,
        OHMGTestCase.fixture_session_prep_no_split,
        OHMGTestCase.fixture_session_prep_split,
        OHMGTestCase.fixture_document_split_results,
        OHMGTestCase.fixture_document_links_split,
    ]

    def test_georef_session(self):

        document = Document.objects.get(pk=5)
        user = get_user_model().objects.get(username="admin")

        session = GeorefSession.objects.create(
            doc=document,
            user=user,
        )

        input_gcp_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            -92.44538695899614,
                            31.312902143444333
                        ]
                    },
                    "properties": {
                        "id": "1d613210-4114-4b58-8d28-839b26867c68",
                        "note": "",
                        "image": [
                            3547,
                            3173
                        ],
                        "listId": 1,
                        "username": "admin"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            -92.44657641570406,
                            31.311858470117244
                        ]
                    },
                    "properties": {
                        "id": "80a64c7f-85e6-40f8-bc29-5709681e03d8",
                        "note": "",
                        "image": [
                            3564,
                            6276
                        ],
                        "listId": 2,
                        "username": "admin"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            -92.44718721779732,
                            31.312339110585995
                        ]
                    },
                    "properties": {
                        "id": "fab611f5-cf0d-4409-81a2-ebb59b7acfba",
                        "note": "",
                        "image": [
                            2004,
                            6243
                        ],
                        "listId": 3,
                        "username": "admin"
                    }
                }
            ]
        }
        session.data['epsg'] = 3857
        session.data['gcps'] = input_gcp_geojson
        session.data['transformation'] = "poly1"
        session.save(update_fields=["data"])
        session.run()

        self.assertEqual(document.status, "georeferenced")

        layer = document.get_layer()
        self.assertIsNotNone(layer)

        self.assertTrue(filecmp.cmp(self.image_alex_p2__2_lyr, layer.file.path, shallow=False))

        del document.gcp_group
        self.assertIsNotNone(document.gcp_group)
        self.assertEqual(len(document.gcp_group.gcps), 3)

        # need to delete listId before comparison as it is not returned by as_geojson
        for i in input_gcp_geojson["features"]:
            del i["properties"]["listId"]
        self.assertEqual(document.gcp_group.as_geojson, input_gcp_geojson)
