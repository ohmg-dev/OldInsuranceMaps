import logging

from django.db.models import signals
from django.dispatch import receiver

from ohmg.core.models import (
    Document,
    Region,
    Layer,
)

logger = logging.getLogger(__name__)

@receiver([signals.post_delete, signals.post_save], sender=Document)
@receiver([signals.post_delete, signals.post_save], sender=Region)
@receiver([signals.post_delete, signals.post_save], sender=Layer)
def update_item_lookup(sender, instance, **kwargs):
    if not hasattr(instance, 'skip_map_lookup_update') or instance.skip_map_lookup_update is False:
        if sender == Document :
            instance.map.update_item_lookup()
        if sender == Region:
            instance.document.map.update_item_lookup()
        if sender == Layer:
            instance.region.document.map.update_item_lookup()


@receiver([signals.post_save], sender=Layer)
def set_georeferenced_on_region(sender, instance, **kwargs):
    instance.region.georeferenced = True
    instance.region.save()


@receiver([signals.post_delete], sender=Layer)
def handle_layer_deletion(sender, instance, **kwargs):

    # set the Region's georeferenced status to False
    instance.region.georeferenced = False
    instance.region.save()

    # delete GCP Group attached to the region
    instance.region.gcp_group.delete()

    # remove layer mask from layerset if present
    if instance.layerset:
        if instance.layerset.multimask:
            if instance.slug in instance.layerset.multimask:
                del instance.layerset.multimask[instance.slug]
                instance.layerset.save()
