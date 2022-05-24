import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.test.client import RequestFactory

from geonode.documents.models import Document
from geonode.layers.models import Layer

from loc_insurancemaps.models import FullThumbnail, Volume
from loc_insurancemaps.renderers import generate_layer_geotiff_thumbnail

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
            ],
            help="the identifier of the LoC resource to add",
        )
        parser.add_argument(
            "--layerid",
            help="the identifier of for the layer",
        )

    def handle(self, *args, **options):

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
