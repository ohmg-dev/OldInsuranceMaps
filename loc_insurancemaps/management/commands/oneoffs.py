import os
import csv
import boto3
from pathlib import Path

from django.db.models.functions import Lower
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.test.client import RequestFactory

from geonode.documents.models import Document
from geonode.layers.models import Layer

from loc_insurancemaps.models import FullThumbnail, Volume, Place
from loc_insurancemaps.renderers import generate_layer_geotiff_thumbnail

from loc_insurancemaps.enumerations import STATE_CHOICES

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "fix-full-thumbnails",
                "fix-document-thumbnails",
                "fix-layer-thumbnails",
                "generate-500.html",
                "initialize-s3-bucket",
                "migrate-places",
                "connect-volumes-to-places",
            ],
            help="the identifier of the LoC resource to add",
        )
        parser.add_argument(
            "--layerid",
            help="the identifier of for the layer",
        )

    def handle(self, *args, **options):

        print(f"operation: {options['operation']}")

        if options['operation'] == "fix-full-thumbnails":
            docs = Document.objects.all()
            print(f"{docs.count()} documents")
            ext = 0
            new = 0
            for d in docs:
                if "missing" in d.thumbnail_url:
                   print(d)
                try:
                    thumb = FullThumbnail.objects.get(document=d)
                    thumb.save()
                    ext += 1
                except FullThumbnail.DoesNotExist:
                    thumb = FullThumbnail(document=d)
                    thumb.save()
                    new += 1
                #d.thumbnail_url = thumb.image.url
                #d.save(update_fields=["thumbnail_url"])
            print(f"{ext} existing FullThumbnails")
            print(f"{new} new FullThumbnails created")

            print("updating all volume lookups...")
            for v in Volume.objects.all():
                v.populate_lookups()
            print("complete.")

        if options['operation'] == "fix-document-thumbnails":
            docs = Document.objects.all()
            print(f"{docs.count()} documents")
            mis = 0
            for d in docs:
                if "missing" in d.thumbnail_url:
                    mis += 1
                    d.save()
            print(f"{mis} missing thumbnail(s) created")

        if options['operation'] == "fix-layer-thumbnails":
            if options['layerid'] is not None:
                print(f"forcing regneration of {options['layerid']} thumbnail")
                layers = Layer.objects.filter(alternate=options['layerid'])
            else:
                layers = Layer.objects.all()
                print(f"checking {layers.count()} layers")
                layers = [i for i in layers if "missing" in i.thumbnail_url]
                print(f"{len(layers)} layers with missing thumbnails.")
            fixed = 0
            for l in layers:
                print(f"regenerating thumb for {l.alternate}")
                generate_layer_geotiff_thumbnail(l)
                fixed += 1
            print(f"{fixed} missing thumbnail(s) created")

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
