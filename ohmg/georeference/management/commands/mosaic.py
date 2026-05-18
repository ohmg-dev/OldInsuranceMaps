from argparse import Namespace

from django.core.management.base import BaseCommand

from ohmg.core.models import LayerSet
from ohmg.georeference.mosaicker import Mosaicker
from ohmg.georeference.tasks import create_mosaic_cog, create_mosaic_tileset


class Command(BaseCommand):
    help = "Operations for creating and managing mosaics."

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "generate-cog",
                "generate-tiles",
            ],
            help="the operation to perform",
        )
        parser.add_argument(
            "-i",
            "--mapid",
            help="the identifier of map that holds this layerset",
        )
        parser.add_argument(
            "-c",
            "--category",
            default="main-content",
            help="category of the layerset to work with",
        )
        parser.add_argument(
            "--pk",
            help="a pk can also be used to identify the layerset",
        )
        parser.add_argument(
            "--background",
            action="store_true",
        )
        parser.add_argument(
            "--multiprocessing",
            action="store_true",
        )

    def handle(self, *args, **options):
        options = Namespace(**options)

        if options.pk:
            ls = LayerSet.objects.get(pk=options.pk)
        else:
            ls = LayerSet.objects.get(
                map__identifier=options.mapid, category__slug=options.category
            )

        m = Mosaicker()

        if options.operation == "generate-tiles":
            if options.background:
                create_mosaic_tileset.delay(ls.pk)
            else:
                m.generate_xyz_tiles(ls, use_multiprocessing=options.multiprocessing)
                m.cleanup_files()

        if options.operation == "generate-cog":
            if options.background:
                create_mosaic_cog.delay(ls.pk)
            else:
                m.generate_cog(ls)
                m.cleanup_files()
