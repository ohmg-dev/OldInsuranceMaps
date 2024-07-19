from pathlib import Path

from django.test import TestCase
from ohmg.places.models import Place

fixture_dir = Path(__file__).parent / 'fixtures'

class LoadPlacesTest(TestCase):

    def test_load_places(self):
        
        csv_dir = fixture_dir / 'places' / 'csv'

        Place().bulk_load_from_csv(Path(csv_dir, "place_countries.csv"))
        Place().bulk_load_from_csv(Path(csv_dir, "place_states.csv"))
        Place().bulk_load_from_csv(Path(csv_dir, "place_counties.csv"))
        Place().bulk_load_from_csv(Path(csv_dir, "place_other.csv"))

        self.assertEqual(4, Place.objects.all().count())
