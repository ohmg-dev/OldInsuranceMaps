import logging

from django.db.models import signals
from django.dispatch import receiver

from ohmg.core.models import (
    Document,
    Region,
    Layer,
)
from ohmg.georeference.models import (
    SessionBase,
    PrepSession,
    GeorefSession,
    Document as OldDocument,
    LayerV1,
)
from ohmg.loc_insurancemaps.models import find_volume

logger = logging.getLogger(__name__)

@receiver(signals.pre_delete, sender=SessionBase)
@receiver(signals.pre_delete, sender=PrepSession)
@receiver(signals.pre_delete, sender=GeorefSession)
def session_on_pre_delete(sender, instance, **kwargs):
    """
    Emulate a cancellation of sessions that have not yet been run, i.e. are in
    the input stage. SessionBase and its proxy models must all be linked to
    this receiver, as .delete() is called on each of these models in various
    parts of the app.

    Reset the document (and layer, if applicable) status to 'prepared' or
    'georeferenced' as appropriate.

    Ultimately, much of this logic should probably be pushed upstream to the
    resource.remove_lock() method, so this receivers only has to call unlock_resources().
    """
    instance.unlock_resources()
    if instance.doc and instance.stage == "input":
        existing_layer = instance.doc.get_layer()
        if instance.type == "p":
            new_status = "unprepared"
        elif instance.type == "g":
            if existing_layer:
                new_status = 'georeferenced'
            else:
                new_status = 'prepared'

        if existing_layer:
            logger.info(f"{instance.__str__()} | delete session and set layer {existing_layer.pk} - '{new_status}'")
            existing_layer.set_status(new_status)

        logger.info(f"{instance.__str__()} | delete session and set document {instance.doc.pk} - '{new_status}'")
        instance.doc.set_status(new_status)

@receiver([signals.post_delete, signals.post_save], sender=OldDocument)
@receiver([signals.post_delete, signals.post_save], sender=LayerV1)
def refresh_volume_lookup(sender, instance, **kwargs):
    volume = find_volume(instance)
    if volume is not None:
        if sender == OldDocument:
            volume.update_doc_lookup(instance)
        if sender == LayerV1:
            volume.update_lyr_lookup(instance)

@receiver([signals.post_delete, signals.post_save], sender=Document)
@receiver([signals.post_delete, signals.post_save], sender=Region)
@receiver([signals.post_delete, signals.post_save], sender=Layer)
def update_item_lookup(sender, instance, **kwargs):
    if sender == Document:
        instance.map.update_item_lookup()
    if sender == Region:
        instance.document.map.update_item_lookup()
    if sender == Layer:
        instance.region.document.map.update_item_lookup()
