from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from loc_insurancemaps.tasks import generate_mosaic_geotiff_as_task
from loc_insurancemaps.management.volume import import_volume, generate_mosaic_geotiff
from loc_insurancemaps.models import Volume

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "import",
                "refresh-lookups",
                "make-sheets",
                "generate-mosaic",
            ],
            help="the operation to perform",
        ),
        parser.add_argument(
            "-i", "--identifier",
            help="the identifier of the LoC resource to add",
        ),
        parser.add_argument(
            "--load-documents",
            action="store_true",
            help="boolean to indicate whether documents should be made for the sheets",
        ),
        parser.add_argument(
            "--background",
            action="store_true",
            help="run the operation in the background with celery"
        )

    def handle(self, *args, **options):

        i = options['identifier']
        if options['operation'] == "refresh-lookups":
            if i is not None:
                vols = Volume.objects.filter(pk=i)
            else:
                vols = Volume.objects.all()
            for v in vols:
                v.populate_lookups()
            print(f"refreshed lookups on {len(vols)} volumes")
        if options['operation'] == "import":
            vol = import_volume(i)
            print(vol)
        if options['operation'] == "make-sheets":
            vol = Volume.objects.get(pk=i)
            vol.make_sheets()
            if options['load_documents']:
                vol.loaded_by = get_user_model().objects.get(username="admin")
                vol.load_date = datetime.now()
                vol.save(update_fields=["loaded_by", "load_date"])
                vol.load_sheet_documents()
        if options['operation'] == "generate-mosaic":
            if i is not None:
                if options['background']:
                    generate_mosaic_geotiff_as_task.apply_async(
                        (i, ),
                        queue="update"
                    )
                else:
                    generate_mosaic_geotiff(i)