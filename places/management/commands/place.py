import csv
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from places.models import Place

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["create", "import-all"],
            help="Name of the new Place.",
        )
        parser.add_argument(
            "--name",
            help="Name of the new Place.",
        )
        parser.add_argument(
            "--parent",
            help="The slug for the parent Place to attach to.",
        )
        parser.add_argument(
            "-c", "--category",
            default="other",
            help="Category for the new Place.",
        )

    def handle(self, *args, **options):

        print(options)
        if options['operation'] == "create":
            self.create_new_place(
                name=options['name'],
                parent=options['parent'],
                category=options['category'],
            )
        elif options['operation'] == "import-all":
            self.import_all_places()

    def create_new_place(self, name, parent_slug, category):

        parent = Place.objects.get(slug=parent_slug)

        place = Place(
            name=name,
            category=category,
        )
        place.save(set_slug=False)
        place.direct_parents.add(parent)
        place.save()
        print(place)

    def import_all_places(self):

        datadir = Path(Path(__file__).parent.parent.parent, "reference_data")
        Place.objects.all().delete()
        def load_place_csv(filepath):
            print(filepath)
            with open(filepath, "r") as op:
                reader = csv.DictReader(op)
                with transaction.atomic():
                    for n, row in enumerate(reader, start=1):
                        parents = row.pop("direct_parents")
                        if n % 100 == 0:
                            print(n)
                        p = Place.objects.create(**row)
                        if parents:
                            for parent in parents.split(","):
                                p.direct_parents.add(parent)
                        p.save(set_slug=True)

        load_place_csv(Path(datadir, "place_countries.csv"))
        load_place_csv(Path(datadir, "place_states.csv"))
        load_place_csv(Path(datadir, "place_counties.csv"))
        load_place_csv(Path(datadir, "place_other.csv"))
