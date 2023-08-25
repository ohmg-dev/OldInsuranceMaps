import logging

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from ohmg.loc_insurancemaps.models import Place

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            help="Name of the new Place.",
        )
        parser.add_argument(
            "parent",
            help="The slug for the parent Place to attach to.",
        )
        parser.add_argument(
            "-c", "--category",
            default="other",
            help="Category for the new Place.",
        )

    def handle(self, *args, **options):

        print(options)
        name = options['name']
        parent_slug = options['parent']
        category = options['category']

        parent = Place.objects.get(slug=parent_slug)

        place = Place(
            name=name,
            category=category,
        )
        place.save(set_slug=False)
        place.direct_parents.add(parent)
        place.save()
        print(place)
