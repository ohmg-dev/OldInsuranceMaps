import logging

from django.db.models import signals
from django.dispatch import receiver

from .models import User

logger = logging.getLogger(__name__)


@receiver(signals.post_save, sender=User)
def subscribe_user_to_newsletter(sender, instance, created, **kwargs):
    try:
        from newsletter.models import Newsletter, Subscription

        if created:
            for newsletter in Newsletter.objects.all():
                sub, created = Subscription.objects.get_or_create(
                    user=instance, newsletter=newsletter, defaults={"subscribed": True}
                )
    except (ImportError, RuntimeError):
        pass
