from django.core.management.base import BaseCommand, CommandError # noqa: F401

from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import ItemBase, VirtualResourceSet


class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        cat_lookup = {
            "main": "main",
            "key_map": "key-map",
            "congest_district": "cbd",
            "graphic_map_of_volumes": "volume-key-map",
        }

        for vol in Volume.objects.all():
            for k, v in vol.sorted_layers.items():
                if len(v) > 0:
                    vrscat = cat_lookup[k]
                    vrs, _ = VirtualResourceSet.objects.get_or_create(
                        category_id=vrscat,
                        volume=vol,
                    )
                    if vrs.category.code == "main":
                        vrs.multimask = vol.multimask
                        vrs.save()
                    for i in v:
                        res = ItemBase.objects.filter(slug=i, type="layer")[0]
                        print(res)
                        res.vrs = vrs
                        res.save()
            # handle the nonmaps a little differently because this is marked as a status
            nonmaps = [k for k, v in vol.document_lookup.items() if v['status'] == 'nonmap']
            if len(nonmaps) > 0:
                vrs, _ = VirtualResourceSet.objects.get_or_create(
                    category_id='nonmap',
                    volume=vol,
                )
                for i in nonmaps:
                    res = ItemBase.objects.get(pk=i)
                    res.vrs = vrs
                    res.save()
