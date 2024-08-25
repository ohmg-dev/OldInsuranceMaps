import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ohmg.loc_insurancemaps.models import Volume, Sheet
from ohmg.georeference.models import Document


class Command(BaseCommand):
    help = 'generate various system configuration files that incorporate the '\
           'the current app settings.'
    out_dir = "_system-configs"
    verbose = False

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        missing_sheet = []
        multiple_sheets = []

        for d in Document.objects.all():
            if not d.parent:
                try:
                    s = Sheet.objects.get(doc=d)
                except Sheet.DoesNotExist:
                    missing_sheet.append(d)
                except Sheet.MultipleObjectsReturned:
                    multiple_sheets.append(d)

        print(f"doc has no parent but also no sheet: {len(missing_sheet)}")
        for i in sorted(missing_sheet, key=lambda i: i.title):
            print(i.pk, i)
        print(f"doc has multiple sheets: {len(multiple_sheets)}")
        for i in sorted(multiple_sheets, key=lambda i: i.title):
            print(i.pk, i)