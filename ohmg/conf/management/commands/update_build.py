import secrets

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "command to search the Library of Congress API."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with open(settings.BUILD_FILE, "w") as o:
            o.write(secrets.token_urlsafe(8))
