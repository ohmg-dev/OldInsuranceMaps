import logging

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from georeference.models import GeorefSession

logger = logging.getLogger(__name__)

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

        old_name = options['old-username']
        new_name = options['new-username']

        # lazy username.lower() query operation.
        user = None
        for u in get_user_model().objects.all():
            if u.username.lower() == old_name.lower():
                user = u
                old_name = user.username
                user.username = new_name
                user.save()
                logger.info(f"username updated.")
        logger.info(f"renaming user: {old_name} --> {new_name}")
        if user is None:
            logger.info("no existing user matches this username")

        seshct = 0
        ptct = 0
        for s in GeorefSession.objects.all():
            if not s.data:
                continue
            if not 'features' in s.data['gcps']:
                continue
            gcp_users = set([u['properties']['username'] for u in s.data['gcps']['features']])
            if old_name in gcp_users:
                seshct += 1
                try:
                    with transaction.atomic():
                        for gcp in s.data['gcps']['features']:
                            if gcp['properties']['username'] == old_name:
                                gcp['properties']['username'] = new_name
                                ptct += 1
                        s.save(update_fields=["data"])
                except Exception as e:
                    logger.error(e)
                    raise(e)
        logger.info(f"updated {ptct} GCPs across {seshct} sessions.")