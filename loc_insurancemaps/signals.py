import logging

from django.db.models import signals
from django.dispatch import receiver

from geonode.layers.models import Layer
from geonode.documents.models import Document
from georeference.models import (
    PrepSession,
    GeorefSession,
    TrimSession,
    LayerMask,
)
from georeference.utils import TKeywordManager

from .models import FullThumbnail, get_volume

logger = logging.getLogger(__name__)

# connect the creation of a FullThumbnail to Document post_save signal
@receiver(signals.post_save, sender=Document)
def create_full_thumbnail(sender, instance, **kwargs):
    if bool(instance.doc_file) is False:
        return
    if not FullThumbnail.objects.filter(document=instance).exists():
        thumb = FullThumbnail(document=instance)
        thumb.save()

# triggered whenever a tkeyword is changed on a Document or Layer
@receiver(signals.m2m_changed, sender=Document.tkeywords.through)
@receiver(signals.m2m_changed, sender=Layer.tkeywords.through)
def resource_status_changed(sender, instance, action, **kwargs):
    """Trigger the document_lookup and layer_lookup updates on a volume
    whenever a Document or Layer has its georeferencing status changed."""
    volume = None
    if action == "post_add":
        new_status = TKeywordManager().get_status(instance)
        if new_status is not None:
            model_name = instance._meta.model.__name__
            if model_name == "Document":
                volume = get_volume("document", instance.pk)
                if volume is not None:
                    volume.update_document_lookup(instance.pk)
            if model_name == "Layer":
                volume = get_volume("layer", instance.pk)
                if volume is not None:
                    volume.update_layer_lookup(instance.alternate)

# refresh the lookup if a session is created or deleted.
@receiver([signals.post_delete, signals.post_save], sender=PrepSession)
@receiver([signals.post_delete, signals.post_save], sender=GeorefSession)
@receiver([signals.post_delete, signals.post_save], sender=TrimSession)
def handle_session_deletion(sender, instance, **kwargs):
    if instance.document is not None:
        volume = get_volume("document", instance.document.pk)
        if volume is not None:
            volume.update_document_lookup(instance.document.pk)
    if instance.layer is not None:
        volume = get_volume("layer", instance.layer.pk)
        if volume is not None:
            volume.update_layer_lookup(instance.layer.alternate)

# refresh the lookup for a layer after it is saved.
@receiver(signals.post_save, sender=Layer)
def refresh_layer_lookup(sender, instance, **kwargs):
    volume = get_volume("layer", instance.pk)
    if volume is not None:
        volume.update_layer_lookup(instance.alternate)

# pre_delete, remove the reference to the layer in Volume lookups
# refresh the lookup for a layer after it is saved.
@receiver(signals.pre_delete, sender=Layer)
def remove_layer_from_lookup(sender, instance, **kwargs):
    volume = get_volume("layer", instance.pk)
    if volume is not None:
        if instance.alternate in volume.layer_lookup:
            del volume.layer_lookup[instance.alternate]
        if instance.alternate in volume.ordered_layers['layers']:
            volume.ordered_layers['layers'].remove(instance.alternate)
        if instance.alternate in volume.ordered_layers['index_layers']:
            volume.ordered_layers['index_layers'].remove(instance.alternate)
        volume.save(update_fields=["layer_lookup", "ordered_layers"])

# refresh the layer lookup after a LayerMask is deleted.
@receiver(signals.post_delete, sender=LayerMask)
def refresh_volume_on_layermask_delete(sender, instance, **kwargs):
    volume = get_volume("layer", instance.layer.pk)
    if volume is not None:
        volume.update_layer_lookup(instance.layer.alternate)
