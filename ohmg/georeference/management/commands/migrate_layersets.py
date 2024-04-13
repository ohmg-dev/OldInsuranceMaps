import os
import csv
from datetime import datetime

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError # noqa: F401

from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import ItemBase, AnnotationSet, SetCategory


class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        cat_lookup = {
            "main": "main-content",
            "key_map": "key-map",
            "congest_district": "congested-district-map",
            "graphic_map_of_volumes": "graphic-map-of-volumes",
        }


        mosaic_lookup = []
        for vol in Volume.objects.all():
            print(vol)
            # make sure there is a main-content annotationset for every volume
            main_ls, _ = AnnotationSet.objects.get_or_create(
                category=SetCategory.objects.get(slug="main-content"),
                volume=vol,
            )
            if vol.mosaic_geotiff:
                print("copying over mosaic cog")
                file_path = vol.mosaic_geotiff.path

                print(file_path)
                fname = os.path.basename(file_path)
                mod_time = os.stat(file_path).st_mtime
                mod_date = datetime.fromtimestamp(mod_time)
                mod_date_str = mod_date.strftime("%Y-%m-%d")
                volid, suffix = fname.split("__")

                outname = f"{volid}-main-{mod_date_str}__{suffix}"
                print(outname)

                ## save the mosaic over to annotation set instance with same file name
                with open(file_path, "rb") as openf:
                    main_ls.mosaic_geotiff.save(outname, File(openf))

                mosaic_lookup.append((str(vol), volid, fname, outname))

            for k, v in vol.sorted_layers.items():
                if len(v) > 0:
                    vrscat = cat_lookup[k]
                    ls, _ = AnnotationSet.objects.get_or_create(
                        category=SetCategory.objects.get(slug=vrscat),
                        volume=vol,
                    )
                    print(ls)
                    if ls.category.slug == "main-content":
                        ls.multimask = vol.multimask
                    ls.save()
                    for i in v:
                        res = ItemBase.objects.filter(slug=i, type="layer")[0]
                        print(res)
                        res.vrs = ls
                        res.save()
            # handle the nonmaps a little differently because this is marked as a status
            nonmaps = [k for k, v in vol.document_lookup.items() if v['status'] == 'nonmap']
            if len(nonmaps) > 0:
                vrs, _ = AnnotationSet.objects.get_or_create(
                    category__slug='non-map-content',
                    volume=vol,
                )
                for i in nonmaps:
                    res = ItemBase.objects.get(pk=i)
                    res.vrs = vrs
                    res.save()

        with open(f"logs/mosaic-migration-lookup_{datetime.now()}.csv", "w") as o:
            writer = csv.writer(o)
            writer.writerow(['title', 'id', 'old filename', 'new filename'])
            for i in mosaic_lookup:
                writer.writerow(i)