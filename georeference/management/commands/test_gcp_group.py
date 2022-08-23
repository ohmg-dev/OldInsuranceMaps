import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from geonode.documents.models import Document

from georeference.models.models import GCPGroup
from georeference.georeferencer import Georeferencer

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'
    def add_arguments(self, parser):
        parser.add_argument(
            "--docid",
            default=None,
            help="directory where the image files are stored",
        )
        parser.add_argument(
            "--annofile",
            default=None,
            help="directory where the image files are stored",
        )

    def handle(self, *args, **options):

        print(options['annofile'])

        user = get_user_model().objects.get(username='admin')

        if options['docid']:
            doc = Document.objects.get(id=options['docid'])

            with open(options['annofile'], "r") as o:
                anno = json.loads(o.read())

            gcp_group = GCPGroup().save_from_annotation(anno, doc, user)
