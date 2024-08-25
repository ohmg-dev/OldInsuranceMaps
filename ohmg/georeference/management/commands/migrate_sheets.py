from django.core.management.base import BaseCommand, CommandError # noqa: F401

from ohmg.core.models import Resource
from ohmg.loc_insurancemaps.models import Sheet
from ohmg.georeference.models import ItemBase, LayerSet, LayerSetCategory


class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        for sheet in Sheet.objects.all():
            print(sheet)
