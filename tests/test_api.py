from .base import OHMGTestCase


class APITestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.Fixtures.admin_user,
        OHMGTestCase.Fixtures.layerset_categories,
        OHMGTestCase.Fixtures.layerset_categories_sanborn,
        OHMGTestCase.Fixtures.new_iberia_place,
        OHMGTestCase.Fixtures.new_iberia_map,
        OHMGTestCase.Fixtures.new_iberia_docs,
        OHMGTestCase.Fixtures.new_iberia_regs,
        OHMGTestCase.Fixtures.new_iberia_main_layerset,
        OHMGTestCase.Fixtures.new_iberia_lyr,
        OHMGTestCase.Fixtures.prepsession_new_iberia_p1_split,
        OHMGTestCase.Fixtures.prepsession_new_iberia_p2_no_split,
        OHMGTestCase.Fixtures.gcps_new_iberia_p1__1,
        OHMGTestCase.Fixtures.gcpgroup_new_iberia_p1__1,
        OHMGTestCase.Fixtures.georef_session_new_iberia_p1__1,
    ]

    def test_places_endpoint(self):
        response = self.get_api_client().get("/api/beta2/places/")
        self.assertEqual(response.status_code, 200)

    def test_places_geojson_endpoint(self):
        response = self.get_api_client().get("/api/beta2/places/geojson/")
        self.assertEqual(response.status_code, 200)

    def test_maps_endpoint(self):
        response = self.get_api_client().get("/api/beta2/maps/")
        self.assertEqual(response.status_code, 200)

        response = self.get_api_client().get("/api/beta2/maps/", {"locale": "new-iberia-la"})
        self.assertEqual(response.status_code, 200)
