
from django.core.management.base import BaseCommand

from ohmg.georeference.models import LayerV1, LayerSet
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

        # existing_bboxs = LayerV1.objects.all().values_list('slug', 'x0', 'y0', 'x1', 'y1')

        # bbox_lookup = {i[0]: [float(i[1]), float(i[2]), float(i[3]), float(i[4])] for i in existing_bboxs}

        print("re-saving Documents...")
        docs = Document.objects.all()
        docs_ct = docs.count()
        for ct, document in enumerate(docs, start=1):
            print(f"{ct}/{docs_ct} (doc: {document.pk})")
            document.save()

        print("re-saving Regions...")
        regs = Region.objects.all()
        regs_ct = regs.count()
        for ct, region in enumerate(regs, start=1):
            print(f"{ct}/{regs_ct} (reg: {region.pk})")
            region.save()

        print("re-saving Layers...")
        lyrs = Layer.objects.all()
        lyrs_ct = lyrs.count()
        for ct, layer in enumerate(lyrs, start=1):
            print(f"{ct}/{lyrs_ct} (lyr: {layer.pk})")
            layer.save()

        print("re-saving LayerSets...")
        layersets = Layer.objects.all()
        layersets_ct = layersets.count()
        for ct, layerset in enumerate(layersets, start=1):
            print(f"{ct}/{layersets_ct} (ls: {layerset.pk})")
            layerset.save()

        print("updating all Map lookups...")
        maps = Map.objects.all().prefetch_related()
        maps_ct = maps.count()
        for ct, map in enumerate(maps, start=1):
            print(f"{ct}/{maps_ct} (map: {map.pk})")
            if map.documents:
                if all([i.file is not None for i in map.documents.all()]):
                    map.set_status("ready")
            map.update_item_lookup()