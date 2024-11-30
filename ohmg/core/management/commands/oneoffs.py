import os
import json
from django.core.management.base import BaseCommand

from ohmg.georeference.models import LayerSet
from ohmg.core.models import (
    Layer, Map, Document, Region
)
from ohmg.georeference.models import GeorefSession, LayerSet

class Command(BaseCommand):
    help = 'add oneoff operations to this command as needed.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "backfill-document-sources",
            ],
            help="Choose what operation to run."
        )

    def handle(self, *args, **options):

        ## 11/20/2024 this operation created to update all existing Map.document_sources fields
        ## after the shape of that field had been changed (page number now stored within each entry)
        if options["operation"] == "backfill_document_sources":

            def get_page_number_from_url(url):
                filename = url.split("/")[-1]
                name = os.path.splitext(filename)[0]
                page_number = name.split("-")[-1].lstrip("0")
                if page_number == "":
                    page_number = "0"

                return page_number

            def old_ds_to_new(file_set):
                source = {
                    "path": None,
                    "iiif_info": None,
                    "page_number": None,
                }
                for entry in file_set:
                    if entry["mimetype"] == "image/jp2":
                        source["path"] = (url := entry.get("url"))
                        source["page_number"] = get_page_number_from_url(url)
                        source["iiif_info"] = entry.get("info")

                return source

            maps = Map.objects.all()

            for map in maps:
                docs = map.document_sources
                new_ds_list = []
                for ds in docs:
                    if isinstance(ds, dict):
                        new_ds_list.append(ds)
                    else:
                        new_ds = old_ds_to_new(ds)
                        new_ds_list.append(new_ds)
                print(json.dumps(new_ds_list, indent=2))
                map.document_sources = new_ds_list
                map.save()
#                print(map, len(map.document_sources), map.documents.all().count())
