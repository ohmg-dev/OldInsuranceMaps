
from django.core.management.base import BaseCommand

from ohmg.georeference.models import LayerSet
from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
    Layer,
)


class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        # bbox_lookup = {i[0]: [float(i[1]), float(i[2]), float(i[3]), float(i[4])] for i in existing_bboxs}

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