from django.core.management.base import BaseCommand, CommandError

from ohmg.georeference.models import GCP, GCPGroup

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def handle(self, *args, **options):

        g = GCP.objects.all()
        print(f"removing {g.count()} GCP objects")
        g.delete()

        g = GCPGroup.objects.all()
        print(f"removing {g.count()} GCPGroup objects")
        g.delete()
