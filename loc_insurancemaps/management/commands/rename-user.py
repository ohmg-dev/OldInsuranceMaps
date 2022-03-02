import os
import csv
from re import S

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from georeference.models import GeoreferenceSession

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "old-username",
            help="the existing username to be changed.",
        )
        parser.add_argument(
            "new-username",
            help="the new name for the user.",
        )

    def handle(self, *args, **options):

        # lazy username.lower() query operation.
        user = None
        for u in get_user_model().objects.all():
            if u.username.lower() == options['old-username'].lower():
                user = u
        if user is None:
            print("no existing user matches this username")
            exit()

        old_name = user.username
        new_name = options['new-username']

        for s in GeoreferenceSession.objects.all():
            gcp_users = set([u['properties']['username'] for u in s.gcps_used['features']])
            if old_name in gcp_users:
                try:
                    with transaction.atomic():
                        print(f"updating gcps_used in GeoreferenceSession {s.pk}...")
                        ct = 0
                        for gcp in s.gcps_used['features']:
                            if gcp['properties']['username'] == old_name:
                                gcp['properties']['username'] = new_name
                                ct += 1
                        print(f"  {ct} updated.")
                        s.save(update_fields=["gcps_used"])
                        print(f"changing username {old_name} --> {new_name}...")
                        user.username = new_name
                        user.save()
                        print(f"  update successful.")
                except Exception as e:
                    raise(e)
