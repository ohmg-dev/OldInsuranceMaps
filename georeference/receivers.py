import logging

from django.db.models import signals
from django.dispatch import receiver

from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
)

logger = logging.getLogger(__name__)

@receiver(signals.pre_delete, sender=PrepSession)
def prepsession_on_pre_delete(sender, instance, **kwargs):
    """
    Emulate a cancellation of sessions that have not yet been run, i.e. are in
    the input stage.
    
    Reset the document status to 'unprepared'.
    """
    instance.unlock_resources()
    if instance.doc and instance.stage == "input":
        logger.info(f"{instance.__str__()} | delete session and set document {instance.doc.pk} - 'unprepared'")
        instance.doc.set_status("unprepared")

@receiver(signals.pre_delete, sender=GeorefSession)
def georefsession_on_pre_delete(sender, instance, **kwargs):
    """
    Emulate a cancellation of sessions that have not yet been run, i.e. are in
    the input stage.
    
    Reset the document status to 'unprepared'.
    """
    instance.unlock_resources()
    # TODO: determine possible existing statuses of instance.doc and instance.lyr
    # and then reset status appropriately based on each scenario
    # if instance.doc and instance.stage == "input":
    #     logger.info(f"{instance.__str__()} | delete session and set document {instance.doc.pk} - 'unprepared'")
    #     instance.doc.set_status("unprepared")
