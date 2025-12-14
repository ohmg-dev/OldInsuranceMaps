import logging

from django.db.models import signals
from django.dispatch import receiver

from .models import SessionBase

logger = logging.getLogger(__name__)


@receiver(signals.post_save, sender=SessionBase)
def update_user_sesh_cts_on_save(sender, instance, created, **kwargs):
    if created and instance.user:
        instance.user.update_sesh_counts()


@receiver(signals.post_delete, sender=SessionBase)
def update_user_sesh_cts_on_delete(sender, instance, **kwargs):
    if instance.user:
        instance.user.update_sesh_counts()
