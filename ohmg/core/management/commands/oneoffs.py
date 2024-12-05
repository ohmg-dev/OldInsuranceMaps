import os
import json
from django.core.management.base import BaseCommand

from ohmg.georeference.models import LayerSet
from ohmg.core.models import Map


class Command(BaseCommand):
    help = "add oneoff operations to this command as needed."

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "backfill-document-sources",
                "resave-content",
            ],
            help="Choose what operation to run.",
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

        ## generally helpful operation during development to go though and run
        ## save() on all objects in the core data model
        if options["operation"] == "resave_content":
            maps = Map.objects.all()
            maps_ct = maps.count()
            for n, map in enumerate(maps, start=1):
                print(map.title, map.pk, f"({n}/{maps_ct})")
                print("re-saving Documents...")
                docs = map.documents.all()
                docs_ct = docs.count()
                for ct, document in enumerate(docs, start=1):
                    print(f"{ct}/{docs_ct} (doc: {document.pk})")
                    document.save(skip_map_lookup_update=True)
                if all([i.file is not None for i in docs]):
                    map.set_status("ready")

                print("re-saving Regions...")
                regs = map.regions.all()
                regs_ct = regs.count()
                for ct, region in enumerate(regs, start=1):
                    print(f"{ct}/{regs_ct} (reg: {region.pk})")
                    region.save(skip_map_lookup_update=True)

                print("re-saving Layers...")
                lyrs = map.layers.all()
                lyrs_ct = lyrs.count()
                for ct, layer in enumerate(lyrs, start=1):
                    print(f"{ct}/{lyrs_ct} (lyr: {layer.pk})")
                    layer.save(skip_map_lookup_update=True)

                print("re-saving LayerSets...")
                layersets = LayerSet.objects.filter(map=map)
                for ct, layerset in enumerate(layersets, start=1):
                    print(f"{layerset} (ls: {layerset.pk})")
                    layerset.save()

                print("updating item lookups...")
                map.update_item_lookup()