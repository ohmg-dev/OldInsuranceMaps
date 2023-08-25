from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ohmg.loc_insurancemaps.models import Volume

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "username"
        )
        parser.add_argument(
            "-c",
            "--city",
            help="city name of volume",
        )
        parser.add_argument(
            "-y",
            "--year",
            help="year of volume",
        )
        parser.add_argument(
            "-n",
            "--number",
            help="volume number",
        )

    def handle(self, *args, **options):

        user = get_user_model().objects.get(username=options['username'])

        volume = Volume.objects.get(
            city=options['city'],
            year=int(options['year']),
            volume_no=options['number']
        )

        confirm = input(f"volume found: {volume}\nsheets: {len(volume.sheets)}\nset user to {user.username}? Y/n")
        if confirm.lower().startswith("n"):
            exit()


        print(f"{volume} -- {volume.loaded_by} -> {user.username}")
        volume.loaded_by = user
        volume.save()
        for sheet in volume.sheets:
            print(f"{sheet.document} -- {sheet.document.owner} -> {user.username}")
            sheet.document.owner = user
            sheet.document.save()
