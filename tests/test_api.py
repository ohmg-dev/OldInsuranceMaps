from .base import OHMGTestCase, get_api_client


class APITestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.fixture_default_layerset_categories,
        OHMGTestCase.fixture_sanborn_layerset_categories,
        OHMGTestCase.fixture_admin_user,
        OHMGTestCase.fixture_alexandria_place,
        OHMGTestCase.fixture_alexandria_map,
        OHMGTestCase.fixture_alexandria_docs,
        OHMGTestCase.fixture_alexandria_regs,
        OHMGTestCase.fixture_alexandria_main_layerset,
        OHMGTestCase.fixture_alexandria_lyr,
        OHMGTestCase.fixture_session_prep_no_split,
        OHMGTestCase.fixture_session_prep_split,
        OHMGTestCase.fixture_document_georef_results_gcpgroup,
        OHMGTestCase.fixture_document_georef_results_gcps,
        OHMGTestCase.fixture_session_georef,
    ]

    def test_places_endpoint(self):
        response = get_api_client().get("/api/beta2/places/")
        self.assertEqual(response.status_code, 200)

    def test_places_geojson_endpoint(self):
        response = get_api_client().get("/api/beta2/places/geojson/")
        self.assertEqual(response.status_code, 200)

    def test_maps_endpoint(self):
        response = get_api_client().get("/api/beta2/maps/")
        self.assertEqual(response.status_code, 200)

        response = get_api_client().get("/api/beta2/maps/", {"locale": "alexandria-la"})
        self.assertEqual(response.status_code, 200)
