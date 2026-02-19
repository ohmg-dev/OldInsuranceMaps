from django.test import tag
from django.urls import reverse

from .base import OHMGTestCase


@tag("extensions")
class ExtensionsTestCase(OHMGTestCase):
    uploaded_files = [("regions", OHMGTestCase.Files.new_iberia_p1__1)]

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

    def test_rss_feeds(self):
        url = reverse("place-feed-rss", kwargs={"place": "iberia-parish-la"})
        response = self.get_api_client().get(url)
        self.assertEqual(response.status_code, 200)
