from pathlib import Path

from django.test import TestCase

class OHMGTestCase(TestCase):

    DATA_DIR = Path(__file__).parent / "data"

    fixture_default_layerset = Path('ohmg/georeference/fixtures/default-layerset-categories.json')
    fixture_sanborn_layerset = Path('ohmg/georeference/fixtures/sanborn-layerset-categories.json')
    fixture_admin_user = DATA_DIR / 'fixtures/auth/admin-user.json',
    fixture_alexandria_place = DATA_DIR / 'fixtures/places/alexandria-la-and-parents.json'

    fixture_alexandria_volume = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-volume.json'
    fixture_alexandria_main_layerset = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-main-layerset.json'
    fixture_alexandria_docs = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-docs.json'
    fixture_alexandria_sheets = DATA_DIR / 'fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-sheets.json'

    fixture_session_prep_no_split = DATA_DIR / 'fixtures/georeference/fixture-prepsession-alexandria-la-1892-p3-no-split.json'
    fixture_session_prep_split = DATA_DIR / 'fixtures/georeference/fixture-prepsession-alexandria-la-1892-p2-split.json'
    fixture_session_georef = DATA_DIR / 'fixtures/georeference/fixture-georefsession-alexandria-la-1892-p2__2.json'

    fixture_document_split_results = DATA_DIR / 'fixtures/georeference/fixture-alexandria-la-1892-p2-child-docs.json'
    fixture_document_georef_results = DATA_DIR / 'fixtures/georeference/fixture-alexandria-la-1892-p2__2-lyr.json'

    fixture_document_links_split = DATA_DIR / 'fixtures/georeference/fixture-document-links-split-alexandria-la-1892-p2.json'
    fixture_document_links_georef = DATA_DIR / 'fixtures/georeference/fixture-document-links-georef-alexandria-la-1892-p2__2.json'

    image_alex_p1_original = DATA_DIR / 'files/source_images/alexandria_la_1892_p1.jpg'
    image_alex_p2_original = DATA_DIR / 'files/source_images/alexandria_la_1892_p2.jpg'
    image_alex_p3_original = DATA_DIR / 'files/source_images/alexandria_la_1892_p3.jpg'

    image_alex_p2__1 = DATA_DIR / 'files/split_images/alexandria_la_1892_p2__1.jpg'
    image_alex_p2__2 = DATA_DIR / 'files/split_images/alexandria_la_1892_p2__2.jpg'

    image_alex_p2__2_lyr = DATA_DIR / 'files/layer_tifs/alexandria_la_1892_p2_2__FzWrFg_00.tif'

    thumbnail_dir = DATA_DIR / 'files/thumbnails'
