from django.core.management.base import BaseCommand, CommandError

from loc_insurancemaps.models import Volume

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "refresh-lookups",
            ],
            help="the identifier of the LoC resource to add",
        )

    def handle(self, *args, **options):

        if options['operation'] == "refresh-lookups":
            for v in Volume.objects.all():
                v.populate_lookups()
