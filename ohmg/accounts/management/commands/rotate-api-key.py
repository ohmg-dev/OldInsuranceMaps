import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import generate_key

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Rotates the core API key used for internal calls."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        key = generate_key()
        with open(settings.OHMG_API_KEY_FILEPATH, "w") as o:
            o.write(key)
        print(f"New default API key saved to {settings.OHMG_API_KEY_FILEPATH}")
        print("You must restart the webserver for this change to take effect.")
        print("Until you do so, the old API key will continue to work.")
