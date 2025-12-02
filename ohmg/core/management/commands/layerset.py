from argparse import Namespace

from django.core.management.base import BaseCommand

from ohmg.core.models import LayerSet


class Command(BaseCommand):
    help = "Operations for managing LayerSets objects."

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "inspect",
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
