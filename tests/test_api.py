from ohmg.places.utils import reset_volume_counts
from ohmg.loc_insurancemaps.models import Volume

from .base import OHMGTestCase, get_api_client


class APITestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
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
        OHMGTestCase.fixture_document_georef_results_lyr,
        OHMGTestCase.fixture_document_georef_results_gcpgroup,
        OHMGTestCase.fixture_document_georef_results_gcps,
        OHMGTestCase.fixture_session_georef,
        OHMGTestCase.fixture_document_links_georef,
    ]

    def test_places_endpoint(self):
        response = get_api_client().get("/api/beta2/places/")
        self.assertEqual(response.status_code, 200)

    def test_places_geojson_endpoint(self):
        reset_volume_counts()
        for v in Volume.objects.all():
            v.update_status("ready")
            v.refresh_lookups()
        response = get_api_client().get("/api/beta2/places/geojson/")
        self.assertEqual(response.status_code, 200)

    def test_maps_endpoint(self):
        reset_volume_counts()
        for v in Volume.objects.all():
            v.update_status("ready")
            v.refresh_lookups()
        response = get_api_client().get("/api/beta2/maps/")
        self.assertEqual(response.status_code, 200)

        response = get_api_client().get("/api/beta2/maps/", {"locale": "alexandria-la"})
        self.assertEqual(response.status_code, 200)
