import csv
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ohmg.core.utils.cli import confirm_continue


class Command(BaseCommand):
    help = (
        "Exports a simple CSV of all users that need to be added to the "
        "newsletter. After export, the added_to_newsletter field is set True."
    )

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        fname = datetime.today().strftime("subscribers-to-add_%Y-%m-%d.csv")
        with open(fname, "w") as o:
            writer = csv.writer(o)
            writer.writerow(["username", "email", "first_name", "last_name", "date_joined"])
            for user in get_user_model().objects.filter(added_to_newsletter=False):
                print(user.username)
                writer.writerow(
                    [user.username, user.email, user.first_name, user.last_name, user.date_joined]
                )
        if confirm_continue("Set these users as added_to_newsletter=True?"):
            for user in get_user_model().objects.filter(added_to_newsletter=False):
                user.added_to_newsletter = True
                user.save()
