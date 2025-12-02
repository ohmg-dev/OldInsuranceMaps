import json

from .base import OHMGTestCase


class APITestCase(OHMGTestCase):
    fixtures = [
        OHMGTestCase.Fixtures.admin_user,
        OHMGTestCase.Fixtures.layerset_categories,
        OHMGTestCase.Fixtures.layerset_categories_sanborn,
        OHMGTestCase.Fixtures.region_categories,
        OHMGTestCase.Fixtures.region_categories_sanborn,
        OHMGTestCase.Fixtures.new_iberia_place,
        OHMGTestCase.Fixtures.new_iberia_map,
        OHMGTestCase.Fixtures.new_iberia_docs,
        OHMGTestCase.Fixtures.gcps_new_iberia_p1__1,
        OHMGTestCase.Fixtures.gcpgroup_new_iberia_p1__1,
        OHMGTestCase.Fixtures.new_iberia_reg_1__1_georef,
        OHMGTestCase.Fixtures.new_iberia_reg_1__2,
        OHMGTestCase.Fixtures.new_iberia_reg_1__3,
        OHMGTestCase.Fixtures.new_iberia_reg_2,
        OHMGTestCase.Fixtures.new_iberia_main_layerset,
        OHMGTestCase.Fixtures.new_iberia_lyr,
        OHMGTestCase.Fixtures.prepsession_new_iberia_p1_split,
        OHMGTestCase.Fixtures.prepsession_new_iberia_p2_no_split,
        OHMGTestCase.Fixtures.georef_session_new_iberia_p1__1,
    ]

    def test_users_endpointt(self):
        response = self.get_api_client().get("/api/beta2/users/")
        self.assertEqual(response.status_code, 200)

    def test_places_endpoint(self):
        response = self.get_api_client().get("/api/beta2/places/")
        self.assertEqual(response.status_code, 200)

    def test_places_geojson_endpoint(self):
        response = self.get_api_client().get("/api/beta2/places/geojson/")
        self.assertEqual(response.status_code, 200)

    def test_map_endpoint(self):
        response = self.get_api_client().get("/api/beta2/map/?map=sanborn03375_001")
        self.assertEqual(response.status_code, 200)

    def test_maps_endpoint(self):
        response = self.get_api_client().get("/api/beta2/maps/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

        response = self.get_api_client().get("/api/beta2/maps/", {"locale": "new-iberia-la"})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

    def test_get_sessions_endpoint(self):
        response = self.get_api_client().get("/api/beta2/sessions/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["count"], 3)

        response2 = self.get_api_client().get(
            "/api/beta2/sessions/?date_range=2024-12-28,2024-12-29"
        )

        data2 = json.loads(response2.content)
        self.assertEqual(data2["count"], 0)

        response3 = self.get_api_client().get(
            "/api/beta2/sessions/?date_range=2024-12-30,2024-12-30"
        )

        data3 = json.loads(response3.content)
        self.assertEqual(data3["count"], 3)

    def test_get_layerset_endpoint(self):
        response = self.get_api_client().get(
            "/api/beta2/layerset/?map=sanborn03375_001&category=main-content"
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["map_id"], "sanborn03375_001")
