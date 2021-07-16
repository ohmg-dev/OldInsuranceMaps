from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.documents.models import Document

from georeference.models import SplitSession, SplitLink

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def handle(self, *args, **options):

        docs = Document.objects.all()
        print(f"removing {docs.count()} Document objects")
        docs.delete()

        ss = SplitSession.objects.all()
        print(f"removing {ss.count()} SplitSession objects")
        ss.delete()

        sl = SplitLink.objects.all()
        print(f"removing {sl.count()} SplitLink objects")
        sl.delete()
