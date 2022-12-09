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
    
    Reset the document status to 'prepared' or 'georeferenced'.
    """
    instance.unlock_resources()
    if instance.doc and instance.stage == "input":
        existing_layer = instance.doc.get_layer()
        if existing_layer:
            new_status = 'georeferenced'
            logger.info(f"{instance.__str__()} | delete session and set document {instance.doc.pk} - '{new_status}'")
            instance.doc.set_status(new_status)
            logger.info(f"{instance.__str__()} | delete session and set layer {existing_layer.pk} - '{new_status}'")
            existing_layer.set_status(new_status)
        else:
            new_status = 'prepared'
            logger.info(f"{instance.__str__()} | delete session and set document {instance.doc.pk} - '{new_status}'")
            instance.doc.set_status(new_status)
        
