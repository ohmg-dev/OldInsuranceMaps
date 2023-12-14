import csv
import time
import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from ohmg.places.models import Place

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'bulk load volumes from csv file'

    def add_arguments(self, parser):
        parser.add_argument(
            "csv",
            help="csv file with ids to load",
        )

    def handle(self, *args, **options):


        data = []
        with open(options['csv'], 'r') as op:
            reader = csv.reader(op)
            next(reader)
            for i in reader:

                if "http" in i[0]:
                    segs = i[0].split('/')
                    ii = [l for l in segs if "sanborn" in l][0]
                else:
                    ii = i
                data.append((ii, i[1]))
        for d in data:
            print(d)
            locale = Place.objects.get(slug=d[1])
            print(locale)
            call_command("volume", "import", identifier=d[0], locale=d[1])
            time.sleep(5)
