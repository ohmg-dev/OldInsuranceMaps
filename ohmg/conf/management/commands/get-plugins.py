from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Download any plugin assets listed in settings.py to static dir."

    def handle(self, *args, **options):
        dest = Path("ohmg/frontend/static/plugins")
        dest.mkdir(exist_ok=True)

        for url in settings.PLUGIN_ASSETS:
            response = requests.get(url)
            print(url)
            with open(Path(dest, url.split("/")[-1]), mode="wb") as file:
                file.write(response.content)
