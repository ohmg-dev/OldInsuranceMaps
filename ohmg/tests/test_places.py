from pathlib import Path

from ohmg.places.models import Place
from .base import OHMGTestCase


class LoadPlacesTest(OHMGTestCase):

    def test_load_places(self):
        
        csv_dir = self.DATA_DIR / 'fixtures' / 'places' / 'csv'

        Place().bulk_load_from_csv(Path(csv_dir, "place_countries.csv"))
        Place().bulk_load_from_csv(Path(csv_dir, "place_states.csv"))
        Place().bulk_load_from_csv(Path(csv_dir, "place_counties.csv"))
        Place().bulk_load_from_csv(Path(csv_dir, "place_other.csv"))

        self.assertEqual(4, Place.objects.all().count())
