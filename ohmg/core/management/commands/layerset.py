from argparse import Namespace
from django.core.management.base import BaseCommand
from ohmg.core.models import LayerSet


class Command(BaseCommand):
    help = "command to search the Library of Congress API."

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "inspect",
                "generate-mosaic-cog",
                "generate-mosaic-json",
            ],
            help="the operation to perform",
        )
        parser.add_argument(
            "-i",
            "--identifier",
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
            help="a pk can also be used to identify the layerset",
        )

    def handle(self, *args, **options):
        options = Namespace(**options)

        if options.pk:
            ls = LayerSet.objects.get(pk=options.pk)
        else:
            ls = LayerSet.objects.get(
                map__identifier=options.identifier, category__slug=options.category
            )

        if options.operation == "inspect":
            print(ls.multimask_extent)

        if options.operation == "generate-mosaic-cog":
            if options.background:
                raise NotImplementedError
                # generate_mosaic_cog_task.delay(ls.pk)
            else:
                ls.generate_mosaic_cog()

        if options.operation == "generate-mosaic-json":
            if options.background:
                raise NotImplementedError
                # generate_mosaic_json_task.delay(ls.pk, trim_all=options.trim_all)
            else:
                ls.generate_mosaic_json(trim_all=options.trim_all)
