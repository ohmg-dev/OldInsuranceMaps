
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

        existing_bboxs = LayerV1.objects.all().values_list('slug', 'x0', 'y0', 'x1', 'y1')

        bbox_lookup = {i[0]: [float(i[1]), float(i[2]), float(i[3]), float(i[4])] for i in existing_bboxs}
        
        models = [
            # Document,
            # Region,
            # Layer,
            LayerSet,
        ]
        for model in models:
            print(model)
            instances = model.objects.all()
            for i in instances:
                # if i.slug in bbox_lookup:
                #     i.extent = bbox_lookup[i.slug]
                i.save()
                # for layer in i.layers.all():
                #     if layer.extent:
                #         poly = Polygon().from_bbox(layer.extent)
                #         print(poly)

        # for map in Map.objects.all().prefetch_related():
        #     print(map)
        #     if map.documents:
        #         if all([i.file is not None for i in map.documents.all()]):
        #             map.set_status("ready")
        #     map.update_item_lookup()