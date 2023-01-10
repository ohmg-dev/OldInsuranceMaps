
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from newsletter.models import Newsletter, Subscription

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "newsletter-slug",
            help="identifier for the newsletter to subscribe users to",
        )

    def handle(self, *args, **options):

        for user in get_user_model().objects.all().exclude(username="AnonymousUser"):
            newsletter = Newsletter.objects.get(slug=options['newsletter-slug'])
            sub, created = Subscription.objects.get_or_create(
                user=user,
                newsletter=newsletter,
                defaults={"subscribed": True}
            )
            if created:
                print(sub)