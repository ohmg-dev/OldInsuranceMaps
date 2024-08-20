from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.asgi import ASGIHandler
from django.core.management import call_command
from django.test import tag, Client

from ohmg.core.importers.base import get_importer, SingleFileImporter
from ohmg.places.models import Place
from ohmg.places.management.utils import reset_volume_counts
from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models import Document, PrepSession, GeorefSession, DocumentLink

from .base import OHMGTestCase

api_auth_header = {"HTTP_X_API_KEY": settings.OHMG_API_KEY}

class APITestCase(OHMGTestCase):

    fixtures = [
        OHMGTestCase.fixture_default_layerset,
        OHMGTestCase.fixture_sanborn_layerset,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_volume,
        OHMGTestCase.fixture_alexandria_docs,
        OHMGTestCase.fixture_alexandria_sheets,
        OHMGTestCase.fixture_alexandria_main_layerset,
        OHMGTestCase.fixture_session_prep_no_split,
        OHMGTestCase.fixture_session_prep_split,
        OHMGTestCase.fixture_document_split_results,
        OHMGTestCase.fixture_document_links_split,
        OHMGTestCase.fixture_document_georef_results,
        OHMGTestCase.fixture_session_georef,
        OHMGTestCase.fixture_document_links_georef,
    ]

    def test_places_endpoint(self):

        client = Client(**api_auth_header)
        response = client.get("/api/beta/places/")
        self.assertEqual(response.status_code, 200)
    
    def test_places_geojson_endpoint(self):
        reset_volume_counts()
        for v in Volume.objects.all():
            v.update_status("ready")
            v.refresh_lookups()
        client = Client(**api_auth_header)
        response = client.get("/api/beta/places/geojson/")
        self.assertEqual(response.status_code, 200)

    def test_maps_endpoint(self):
        reset_volume_counts()
        for v in Volume.objects.all():
            v.update_status("ready")
            v.refresh_lookups()
        client = Client(**api_auth_header)
        response = client.get("/api/beta/maps/")
        self.assertEqual(response.status_code, 200)

        response = client.get("/api/beta/maps/", {"locale": "alexandria-la"})
        self.assertEqual(response.status_code, 200)
