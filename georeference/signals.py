import logging

from django.db.models import signals
from django.dispatch import receiver

from geonode.layers.models import Style
from geonode.thumbs.thumbnails import create_thumbnail

from georeference.models.resources import (
    GCPGroup,
    LayerMask,
)
from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
)
from georeference.utils import (
    get_gs_catalog,
    TKeywordManager,
)

logger = logging.getLogger(__name__)

@receiver(signals.pre_delete, sender=PrepSession)
def pre_delete_prepsession(sender, instance, **kwargs):
    """
    Emulate a cancellation of sessions that have not yet been run, i.e. are in
    the input stage.
    
    Reset the document status to 'unprepared'.
    """

    if instance.stage == "input" and instance.document is not None:
        logger.info(f"{instance.__str__()} | delete session and set document {instance.document.pk} - 'unprepared'")
        tkm = TKeywordManager()
        tkm.set_status(instance.document, "unprepared")

@receiver(signals.pre_delete, sender=GeorefSession)
def pre_delete_georefsession(sender, instance, **kwargs):
    """
    Emulate a cancellation of sessions that have not yet been run, i.e. are in
    the input stage.
    
    If a GCPGroup exists, assume the document has been georeferenced through 
    a past session, and reset status to 'georeferenced'.
    
    Otherwise, reset to 'prepared'.
    """

    if instance.stage == "input" and instance.document is not None:
        tkm = TKeywordManager()
        if GCPGroup.objects.filter(document=instance.document).exists():
            new_status = "georeferenced"
        else:
            new_status = "prepared"
        logger.info(f"{instance.__str__()} | delete session and set document {instance.document.pk} - '{new_status}'")
        tkm.set_status(instance.document, new_status)
