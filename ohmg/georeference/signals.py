import logging

from django.db.models import signals
from django.dispatch import receiver

from .models import GeorefSession, PrepSession

logger = logging.getLogger(__name__)


@receiver([signals.post_save, signals.post_delete], sender=PrepSession)
@receiver([signals.post_save, signals.post_delete], sender=GeorefSession)
def update_user_sesh_cts(sender, instance, **kwargs):
    if instance.user:
        logger.debug(f"updating session counts for {instance.user.username}")
        instance.user.update_sesh_counts()
