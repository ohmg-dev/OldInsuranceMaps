from django.core.management.base import BaseCommand
from ohmg.loc_insurancemaps.tasks import (
    generate_mosaic_cog_task,
    generate_mosaic_json_task,
)
from ohmg.georeference.models import AnnotationSet

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "generate-mosaic-cog",
                "generate-mosaic-json",
            ],
            help="the operation to perform",
        )
        parser.add_argument(
            "-i", "--identifier",
            help="the identifier of map that holds this layerset",
        )
        parser.add_argument(
            "-c", "--category",
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

        if options['pk']:
            ls = AnnotationSet.objects.get(pk=options['pk'])
        else:
            ls = AnnotationSet.objects.get(volume__identifier=options['identifier'], category=options['category'])

        if options['operation'] == "generate-mosaic-cog":
            if options['background']:
                raise NotImplementedError
                generate_mosaic_cog_task.delay(ls.pk)
            else:
                ls.generate_mosaic_cog()

        if options['operation'] == "generate-mosaic-json":
            if options['background']:
                raise NotImplementedError
                generate_mosaic_json_task.delay(ls.pk, trim_all=options['trim_all'])
            else:
                ls.generate_mosaic_json(trim_all=options['trim_all'])
