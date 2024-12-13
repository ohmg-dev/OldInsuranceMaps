from pathlib import Path
import shutil
from typing import List

from django.conf import settings
from django.test import TestCase, Client


def copy_files_to_media_root(file_paths: List[Path], sub_dir: str = ""):
    dest = Path(settings.MEDIA_ROOT, sub_dir)
    dest.mkdir(exist_ok=True)
    for src in file_paths:
        shutil.copy2(src, dest)


def get_api_client():
    api_auth_header = {"HTTP_X_API_KEY": settings.OHMG_API_KEY}
    return Client(**api_auth_header)


class OHMGTestCase(TestCase):
    DATA_DIR = Path(__file__).parent / "data"

    fixture_default_layerset_categories = Path(
        "ohmg/georeference/fixtures/default-layerset-categories.json"
    )
    fixture_sanborn_layerset_categories = Path(
        "ohmg/georeference/fixtures/sanborn-layerset-categories.json"
    )
    fixture_admin_user = (DATA_DIR / "fixtures/auth/admin-user.json",)
    fixture_alexandria_place = DATA_DIR / "fixtures/places/alexandria-la-and-parents.json"

    fixture_alexandria_volume = (
        DATA_DIR / "fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-volume.json"
    )
    fixture_alexandria_main_layerset = (
        DATA_DIR / "fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-main-layerset.json"
    )
    fixture_alexandria_docs = (
        DATA_DIR / "fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-docs.json"
    )
    fixture_alexandria_sheets = (
        DATA_DIR / "fixtures/loc_insurancemaps/sanborn-alexandria-la-1892-sheets.json"
    )

    fixture_session_prep_no_split = (
        DATA_DIR / "fixtures/georeference/fixture-prepsession-alexandria-la-1892-p3-no-split.json"
    )
    fixture_session_prep_split = (
        DATA_DIR / "fixtures/georeference/fixture-prepsession-alexandria-la-1892-p2-split.json"
    )
    fixture_document_split_results = (
        DATA_DIR / "fixtures/georeference/fixture-alexandria-la-1892-p2-child-docs.json"
    )

    fixture_session_georef = (
        DATA_DIR / "fixtures/georeference/fixture-georefsession-alexandria-la-1892-p2__2.json"
    )
    fixture_document_georef_results_lyr = (
        DATA_DIR / "fixtures/georeference/fixture-alexandria-la-1892-p2__2-lyr.json"
    )
    fixture_document_georef_results_gcpgroup = (
        DATA_DIR / "fixtures/georeference/fixture-alexandria-la-1892-p2__2-gcpgroup.json"
    )
    fixture_document_georef_results_gcps = (
        DATA_DIR / "fixtures/georeference/fixture-alexandria-la-1892-p2__2-gcps.json"
    )

    fixture_document_links_split = (
        DATA_DIR / "fixtures/georeference/fixture-document-links-split-alexandria-la-1892-p2.json"
    )
    fixture_document_links_georef = (
        DATA_DIR
        / "fixtures/georeference/fixture-document-links-georef-alexandria-la-1892-p2__2.json"
    )

    image_alex_p1_original = DATA_DIR / "files/source_images/alexandria_la_1892_p1.jpg"
    image_alex_p2_original = DATA_DIR / "files/source_images/alexandria_la_1892_p2.jpg"
    image_alex_p3_original = DATA_DIR / "files/source_images/alexandria_la_1892_p3.jpg"

    image_alex_p2__1 = DATA_DIR / "files/split_images/alexandria_la_1892_p2__1.jpg"
    image_alex_p2__2 = DATA_DIR / "files/split_images/alexandria_la_1892_p2__2.jpg"

    image_alex_p2__2_lyr = DATA_DIR / "files/layer_tifs/alexandria_la_1892_p2_2__FzWrFg_00.tif"

    thumbnail_dir = DATA_DIR / "files/thumbnails"
