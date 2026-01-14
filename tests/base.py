import shutil
import sys
from pathlib import Path
from typing import List, Tuple

from django.conf import settings
from django.core.management import call_command
from django.test import Client, LiveServerTestCase

from ohmg.core.models import Document, Layer, LayerSet, Map, MapGroup, Region

DATA_DIR = Path(__file__).parent / "data"


class OHMGTestCase(LiveServerTestCase):
    """This inherits from LiveServerTestCase so that there will be a
    localhost:xxxx server running based on the test database."""

    ## On classes that inherit this one, files can be defined
    ## here and they will be copied to uploaded directory before
    ## test run.
    uploaded_files: List[Tuple[str, Path]]
    cleanup_files: List[Tuple[str, str]]

    # DATA_DIR = Path(__file__).parent / "data"

    class Fixtures:
        # DATA_DIR = Path(__file__).parent / "data"

        admin_user = DATA_DIR / "fixtures/auth/admin-user.json"

        layerset_categories = Path("ohmg/core/fixtures/default-layerset-categories.json")
        layerset_categories_sanborn = Path("ohmg/core/fixtures/sanborn-layerset-categories.json")

        region_categories = Path("ohmg/core/fixtures/default-region-categories.json")
        region_categories_sanborn = Path("ohmg/core/fixtures/sanborn-region-categories.json")

        new_iberia_place = DATA_DIR / "fixtures/places/new-iberia-la-and-parents.json"

        new_iberia_map = DATA_DIR / "fixtures/core/new-iberia-1885-map.json"
        new_iberia_docs = DATA_DIR / "fixtures/core/new-iberia-1885-docs.json"
        # new_iberia_regs = DATA_DIR / "fixtures/core/new-iberia-1885-regs.json"
        new_iberia_reg_1__1 = DATA_DIR / "fixtures/core/new-iberia-1885-reg-1__1.json"
        new_iberia_reg_1__1_georef = DATA_DIR / "fixtures/core/new-iberia-1885-reg-1__1-georef.json"
        new_iberia_reg_1__2 = DATA_DIR / "fixtures/core/new-iberia-1885-reg-1__2.json"
        new_iberia_reg_1__3 = DATA_DIR / "fixtures/core/new-iberia-1885-reg-1__3.json"
        new_iberia_reg_2 = DATA_DIR / "fixtures/core/new-iberia-1885-reg-2.json"
        new_iberia_lyr = DATA_DIR / "fixtures/core/new-iberia-1885-lyr.json"
        new_iberia_main_layerset = (
            DATA_DIR / "fixtures/core/new-iberia-1885-main-content-layerset.json"
        )

        prepsession_new_iberia_p1_split = (
            DATA_DIR / "fixtures/sessions/prepsession-new-iberia-1885-p1-split.json"
        )
        prepsession_new_iberia_p2_no_split = (
            DATA_DIR / "fixtures/sessions/prepsession-new-iberia-1885-p2-no-split.json"
        )

        georef_session_new_iberia_p1__1 = (
            DATA_DIR / "fixtures/sessions/georefsesssion-new-iberia-1885-p1__1.json"
        )
        gcps_new_iberia_p1__1 = DATA_DIR / "fixtures/georeference/new-iberia-1885-p1__1-gcps.json"
        gcpgroup_new_iberia_p1__1 = (
            DATA_DIR / "fixtures/georeference/new-iberia-1885-p1__1-gcpgroup.json"
        )

    class Files:
        DATA_DIR = Path(__file__).parent / "data"

        new_iberia_p1_original = DATA_DIR / "files/source_images/new_iberia_la_1885_p1.jpg"
        new_iberia_p2_original = DATA_DIR / "files/source_images/new_iberia_la_1885_p2.jpg"
        new_iberia_p3_original = DATA_DIR / "files/source_images/new_iberia_la_1885_p3.jpg"

        new_iberia_p1__1 = DATA_DIR / "files/regions/new_iberia_la_1885_p1__1.jpg"
        new_iberia_p1__2 = DATA_DIR / "files/regions/new_iberia_la_1885_p1__2.jpg"
        new_iberia_p1__3 = DATA_DIR / "files/regions/new_iberia_la_1885_p1__3.jpg"
        new_iberia_p2_region = DATA_DIR / "files/regions/new_iberia_la_1885_p2.jpg"

        new_iberia_p1__1_lyr = DATA_DIR / "files/layers/new_iberia_la_1885_p1_1__seTn7p_00.tif"

    @classmethod
    def setUpTestData(cls):
        """Even though fixtures have been loaded, need to call save() on each object
        to properly trigger the creation of derivative fields."""

        for cls in [MapGroup, Map, Document, Region, Layer, LayerSet]:
            for obj in cls.objects.all():
                obj.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        uploaded_files = getattr(cls, "uploaded_files", [])
        for subdir, src_path in uploaded_files:
            dest = Path(settings.MEDIA_ROOT, subdir)
            dest.mkdir(exist_ok=True, parents=True)
            shutil.copy2(src_path, dest)

        settings.LOCAL_MEDIA_HOST = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        for subdir in [
            "documents",
            "regions",
            "layers",
            "thumbnails",
            "vrt",
        ]:
            for f in Path(settings.MEDIA_ROOT / subdir).glob("*"):
                f.unlink()
        return super().tearDownClass()

    def get_api_client(self) -> Client:
        api_auth_header = {"HTTP_X_API_KEY": settings.OHMG_API_KEY}
        return Client(**api_auth_header)

    def dump_data(self, model_label: str, outfile: str):
        """Helper function to dump db content to a fixture JSON file during test runs."""

        sysout = sys.stdout
        sys.stdout = open(outfile, "w")
        call_command("dumpdata", model_label, "--indent=2")
        sys.stdout = sysout
