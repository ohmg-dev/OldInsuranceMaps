import os
import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "add oneoff operations to this command as needed."

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "backfill-document-sources",
                "resave-content",
                "clean-uploaded-files",
                "copy-layersets",
                "update-main-content-pk",
                "reverse-region-gcpgroup-relationship",
                "handle-missing-iiif-references-and-documents",
                "set-region-categories",
                "fix-full-region-files",
            ],
            help="Choose what operation to run.",
        )
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--use-multiprocessing", action="store_true")

    def handle(self, *args, **options):
        operation = options["operation"]

        ## 11/20/2024 this operation created to update all existing Map.document_sources fields
        ## after the shape of that field had been changed (page number now stored within each entry)
        if operation == "backfill-document-sources":
            from ohmg.core.models import Map

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
        if operation == "resave-content":
            from ohmg.core.models import LayerSet, Map

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

        ## 12/30/2024 needed this command to clean up disk space on the prod server
        if operation == "clean-uploaded-files":
            from ohmg.core.models import Map, Document, Region, Layer, LayerSet

            media_dir = Path(settings.MEDIA_ROOT)
            files_on_disk = [str(i) for i in media_dir.glob("documents/*") if i.is_file()]
            files_on_disk += [str(i) for i in media_dir.glob("regions/*") if i.is_file()]
            files_on_disk += [str(i) for i in media_dir.glob("layers/*") if i.is_file()]
            files_on_disk += [str(i) for i in media_dir.glob("mosaics/*") if i.is_file()]
            files_on_disk += [str(i) for i in media_dir.glob("thumbnails/*") if i.is_file()]

            all_real_paths = [i.file.path for i in Document.objects.all() if i.file]
            all_real_paths += [i.thumbnail.path for i in Document.objects.all() if i.thumbnail]
            all_real_paths += [i.file.path for i in Region.objects.all() if i.file]
            all_real_paths += [i.thumbnail.path for i in Region.objects.all() if i.thumbnail]
            all_real_paths += [i.file.path for i in Layer.objects.all() if i.file]
            all_real_paths += [i.thumbnail.path for i in Layer.objects.all() if i.thumbnail]
            all_real_paths += [
                i.mosaic_geotiff.path for i in LayerSet.objects.all() if i.mosaic_geotiff
            ]

            rm_paths = []
            match_paths = []
            for path in files_on_disk:
                if path not in all_real_paths:
                    rm_paths.append(path)
                    print(f"to delete: {path}")
                else:
                    match_paths.append(path)

            print(f"files to delete: {len(rm_paths)}")
            print(f"files will be retained: {len(match_paths)}")

            if input("continue? Y/n ").lower().startswith("n"):
                print("-- cancelling operation.")
                exit()

            for rm in rm_paths:
                os.remove(rm)

        ## Jan 23rd, 2025, created during migration of LayerSet from georeference to core app.
        if operation == "copy-layersets":
            from ohmg.core.models import (
                LayerSet as NewLayerSet,
                LayerSetCategory as NewLayerSetCategory,
            )
            from ohmg.georeference.models import (
                LayerSet as OldLayerSet,
                LayerSetCategory as OldLayerSetCategory,
            )

            if options["reset"]:
                NewLayerSet.objects.all().delete()
                NewLayerSetCategory.objects.all().delete()

            cat_lookup = {}
            for lsc_old in OldLayerSetCategory.objects.all():
                lsc, created = NewLayerSetCategory.objects.get_or_create(pk=lsc_old.pk)
                lsc.slug = lsc_old.slug
                lsc.description = lsc_old.description
                lsc.display_name = lsc_old.display_name
                lsc.save()
                cat_lookup[lsc.pk] = lsc

            ls_lookup = {}
            ct = OldLayerSet.objects.all().count()
            for n, ls_old in enumerate(OldLayerSet.objects.all()):
                ls, created = NewLayerSet.objects.get_or_create(pk=ls_old.pk)
                ls.map = ls_old.map
                ls.category = cat_lookup[ls_old.category.pk]
                ls.multimask = ls_old.multimask
                ls.mosaic_geotiff = ls_old.mosaic_geotiff
                ls.mosaic_json = ls_old.mosaic_json
                ls.extent = ls_old.extent
                ls.save()
                ls_lookup[ls.pk] = ls
                if n % 100 == 0:
                    print(f"{n}/{ct}")

            ct = Layer.objects.all().count()
            for n, layer in enumerate(Layer.objects.all()):
                if not layer.layerset:
                    print(layer)
                    continue
                layer.layerset2 = ls_lookup[layer.layerset.pk]
                layer.save(skip_map_lookup_update=True)
                if n % 1000 == 0:
                    print(f"{n}/{ct}")

        ## Feb 5th, 2025, replacing the existing main-content layerset
        ## category with a duplicate that has pk=1 (because current pk=0
        ## is invalid)
        if operation == "update-main-content-pk":
            from ohmg.core.models import LayerSet, LayerSetCategory

            ## 1. create the new category with the correct pk
            ls_main_cat = LayerSetCategory.objects.create(
                pk=1, slug="new-main-content", display_name="Main Content"
            )

            ## 2. update all existing main content layersets to use the
            ## new category
            all_main_ls = LayerSet.objects.filter(category__pk=0)
            for ls in all_main_ls:
                ls.category = ls_main_cat
            LayerSet.objects.bulk_update(all_main_ls, ["category"])

            ## 3. Delete the now unused original Main Content category
            matching = LayerSet.objects.filter(category__slug="main-content")
            print(len(matching))
            if matching.exists():
                raise Exception("there should not be any LS with this category...")

            old_main = LayerSetCategory.objects.get(slug="main-content")
            old_main.delete()

            ## 4. now rename the new category to have the proper slug
            ls_main_cat.slug = "main-content"
            ls_main_cat.save()

        if operation == "reverse-region-gcpgroup-relationship":
            for region in Region.objects.all():
                if region.gcp_group:
                    region.gcp_group.region2 = region
                    region.gcp_group.save()

        if operation == "handle-missing-iiif-references-and-documents":
            maps = Map.objects.all()
            logfile = Path(
                settings.LOG_DIR, f"document-rectification-{int(datetime.now().timestamp())}.txt"
            )
            with open(logfile, "w") as log:
                for map in maps:
                    # clean any completely empty document source entries
                    map.document_sources = [
                        i
                        for i in map.document_sources
                        if (i["iiif_info"] or i["path"] or i["page_number"])
                    ]
                    map.save()

                    # extra work on all loc sanborn maps
                    if map.pk.startswith("sanborn"):
                        print(map)
                        map.iiif_manifest = f"https://loc.gov/item/{map.pk}/manifest.json"
                        for src in map.document_sources:
                            try:
                                d, created = Document.objects.get_or_create(
                                    map=map, page_number=src["page_number"]
                                )
                                d.iiif_info = src["iiif_info"]
                                d.save(skip_map_lookup_update=True)
                                if created:
                                    print(f"document created: {d}")
                            except Exception as e:
                                log.write(
                                    f"{map.pk}, {map} -- document error {src['page_number']}: {e}\n"
                                )

                        map.save()
                        print("updating lookup...")
                        map.update_item_lookup()

        ## March 27th, 2025 -- adding a new field Region.category, which supercedes the exsiting
        ## Region.is_map field (presents more options). This operation must be run right after
        ## making the migration to update all existing Region objects accordingly.
        if operation == "set-region-categories":
            from ohmg.core.models import Region, RegionCategory, Map

            map_cat = RegionCategory.objects.get(slug="map")
            nonmap_cat = RegionCategory.objects.get(slug="non-map")
            regions = Region.objects.all()
            ct = regions.count()
            for n, r in enumerate(regions, start=1):
                if r.is_map:
                    r.category = map_cat
                else:
                    r.category = nonmap_cat
                r.save(skip_map_lookup_update=True)
                print(f"{n}/{ct}")

            print("Region update complete. Updating all Map.item_lookup now.")
            maps = Map.objects.all()
            ct = maps.count()
            for n, map in enumerate(Map.objects.all(), start=1):
                map.update_item_lookup()
                print(f"{map} {n}/{ct}")

        ## June 19th, 2025 -- There was a bug with the S3 code where regions that contained
        ## the whole document image would save that file to /regions/documents/filename.jpg,
        ## instead of /regions/filename.jpg. The code is fixed, but 500 objects on the prod
        ## server need to be fixed.
        if operation == "fix-full-region-files":
            from django.core.files import File
            from ohmg.core.models import Region

            regions = Region.objects.filter(file__startswith="regions/documents/")
            print(regions.count())

            for region in regions:
                proper_name = Path(region.file.name).name
                old_path = region.file.path
                with region.file.open("rb") as openf:
                    region.file.save(proper_name, File(openf))

                os.remove(old_path)
