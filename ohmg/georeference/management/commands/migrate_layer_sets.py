from django.core.management.base import BaseCommand, CommandError # noqa: F401

from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import ItemBase

from ohmg.georeference.models import VirtualResourceSet, VirtualResourceSetType

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        # parser.add_argument(
        #     "operation",
        #     choices=['georeference', 'thumbnail', 'set-extent'],
        #     help="operation to perform",
        # )
        pass

    def handle(self, *args, **options):

        cat_main, _ = VirtualResourceSetType.objects.get_or_create(
            code="main",
            name="Main Content",
            geospatial=True,
        )
        cat_keymap, _ = VirtualResourceSetType.objects.get_or_create(
            code="key-map",
            name="Key Map",
            geospatial=True,
        )
        cat_congest, _ = VirtualResourceSetType.objects.get_or_create(
            code="cbd",
            name="Congested Area",
            geospatial=True,
        )
        cat_vol_keymap, _ = VirtualResourceSetType.objects.get_or_create(
            code="key-map-vol",
            name="Volume Key Map",
            geospatial=True,
        )

        for vol in Volume.objects.all():
            for k, v in vol.sorted_layers.items():
                if len(v) > 0:
                    if k == "main":
                        vrscat = "main"
                    if k == "key_map":
                        vrscat = "key-map"
                    if k == "congest_district":
                        vrscat = "cbd"
                    if k == "graphic_map_of_volumes":
                        vrscat = "key-map-vol"
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
                # print(k, v)
            # print(v.sorted_layers.keys())
            # print(v.multimask)

