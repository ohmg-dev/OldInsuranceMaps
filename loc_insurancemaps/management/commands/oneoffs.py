import os
import csv
import boto3
from pathlib import Path

from django.db import transaction
from django.db.models.functions import Lower
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.test.client import RequestFactory

from loc_insurancemaps.models import Volume, Place

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "generate-500.html",
                "initialize-s3-bucket",
                "migrate-places",
                "connect-volumes-to-places",
                "reset-volume-counts",
            ],
            help="the identifier of the LoC resource to add",
        )
        parser.add_argument(
            "--layerid",
            help="the identifier of for the layer",
        )

    def handle(self, *args, **options):

        print(f"operation: {options['operation']}")

        if options['operation'] == "generate-500.html":
            rf = RequestFactory()
            request = rf.get('/')
            content = render_to_string('500.html.template', request=request)
            outpath = os.path.join(settings.LOCAL_ROOT, "templates/500.html")
            with open(outpath, 'w') as static_file:
                static_file.write(content)
            print(f"file saved to: {outpath}")

        if options['operation'] == "initialize-s3-bucket":
            client = boto3.client("s3", **settings.S3_CONFIG)

            response = client.list_buckets()
            if settings.S3_BUCKET_NAME not in [i['Name'] for i in response['Buckets']]:
                print(f"Creating bucket: {settings.S3_BUCKET_NAME}")
                client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                print("Bucket created.")
            else:
                print(f"Bucket already exists: {settings.S3_BUCKET_NAME}")

        if options['operation'] == "migrate-places":

            datadir = Path(settings.LOCAL_ROOT, "reference_data")
            Place.objects.all().delete()
            def load_place_csv(filepath):
                with open(filepath, "r") as op:
                    reader = csv.DictReader(op)
                    for row in reader:
                        parents = row.pop("direct_parents")
                        print(row)
                        p = Place.objects.create(**row)
                        if parents:
                            for parent in parents.split(","):
                                p.direct_parents.add(parent)
                        p.save(set_slug=True)

            load_place_csv(Path(datadir, "place_countries.csv"))
            load_place_csv(Path(datadir, "place_states.csv"))
            load_place_csv(Path(datadir, "place_counties.csv"))
            load_place_csv(Path(datadir, "place_other.csv"))

        if options['operation'] == "connect-volumes-to-places":

            typo_lookup = {
                "Saint": "St.",
                "Sanit": "St.",
                "Balon": "Baton",
                "La Salle": "LaSalle",
                "Claibrone": "Claiborne",
                "Point Coupee": "Pointe Coupee",
            }

            for volume in Volume.objects.all():
                state_p, parish_p, locale_p = None, None, None
                place_lower = Place.objects.annotate(lower_name=Lower('name'))
                state_p = place_lower.get(category="state", lower_name__iexact=volume.state)
                county_options = state_p.get_descendants()
                for i in county_options:
                    match_str = volume.county_equivalent.replace("County", "").replace("Parish", "").rstrip()
                    for k, v in typo_lookup.items():
                        if k in match_str:
                            match_str = match_str.replace(k, v)
                    if i.name == match_str:
                        parish_p = i
                        break
                if not parish_p:
                    print(volume.county_equivalent)
                else:
                    locale_options = parish_p.get_descendants()
                    for i in locale_options:
                        if i.name == volume.city:
                            locale_p = i
                    if not locale_p:
                        print(volume.city, parish_p, state_p)
                    else:
                        volume.locale = locale_p
                        volume.save()

        if options['operation'] == "reset-volume-counts":

            print("set all Place volume counts to 0")
            Place.objects.all().update(volume_count=0, volume_count_inclusive=0)
            print("done")

            for volume in Volume.objects.all():
                print(volume)
                volume.update_place_counts()