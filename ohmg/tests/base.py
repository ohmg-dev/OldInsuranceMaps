from pathlib import Path

from django.test import TestCase

class OHMGTestCase(TestCase):

    DATA_DIR = Path(__file__).parent / "data"

    fixture_default_layerset = Path('ohmg/georeference/fixtures/default-layerset-categories.json')
    fixture_sanborn_layerset = Path('ohmg/georeference/fixtures/sanborn-layerset-categories.json')
    fixture_admin_user = DATA_DIR / 'fixtures/auth/admin-user.json',
    fixture_alexandria_place = DATA_DIR / 'fixtures/places/alexandria-la-and-parents.json'

    fixture_alexandria_volume = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-volume.json'
    fixture_alexandria_docs = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-docs.json'
    fixture_alexandria_sheets = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-sheets.json'

    image_alex_p1_original = DATA_DIR / 'files/source_images/alexandria_la_1892_p1.jpg'
    image_alex_p2_original = DATA_DIR / 'files/source_images/alexandria_la_1892_p2.jpg'
    image_alex_p3_original = DATA_DIR / 'files/source_images/alexandria_la_1892_p3.jpg'
