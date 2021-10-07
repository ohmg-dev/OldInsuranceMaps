from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document

from georeference.models import (
    GeoreferenceSession, GCP, GCPGroup,
    SplitSession, Segmentation, SplitDocumentLink
)
class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'


    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["reset-all"],
            help="",
        )

    def handle(self, *args, **options):

        if options["operation"] == "reset-all":
            model_list = [
                Document,
                GCP,
                GCPGroup,
                GeoreferenceSession,
                SplitSession,
                Segmentation,
            ]

            for model in model_list:
                objs = model.objects.all()
                print(f"removing {objs.count()} {model.__name__} objects")
                objs.delete()
