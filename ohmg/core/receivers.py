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
    if not hasattr(instance, "skip_map_lookup_update") or instance.skip_map_lookup_update is False:
        if sender == Document:
            instance.map.update_item_lookup()
        if sender == Region:
            instance.document.map.update_item_lookup()
        if sender == Layer:
            instance.region.document.map.update_item_lookup()


@receiver([signals.post_delete], sender=Document)
@receiver([signals.post_delete], sender=Region)
@receiver([signals.post_delete], sender=Layer)
def delete_files(sender, instance, **kwargs):
    instance.thumbnail.delete(save=False)
    instance.file.delete(save=False)


@receiver([signals.post_save], sender=Layer)
def set_georeferenced_on_region(sender, instance, **kwargs):
    if not hasattr(instance, "skip_map_lookup_update") or instance.skip_map_lookup_update is False:
        instance.region.georeferenced = True
        instance.region.save()


@receiver([signals.post_delete], sender=Layer)
def handle_layer_deletion(sender, instance, **kwargs):
    # set the Region's georeferenced status to False
    instance.region.georeferenced = False
    instance.region.save()

    # delete GCP Group attached to the region
    try:
        instance.region.gcpgroup.delete()
    except Exception as e:
        logger.warning(f"instance.region.gcpgroup.delete(): {e}")

    # remove layer mask from layerset if present
    if instance.layerset2:
        if instance.layerset2.multimask:
            if instance.slug in instance.layerset2.multimask:
                del instance.layerset2.multimask[instance.slug]
                instance.layerset2.save()

    # remove layerset if this was the last layer attached to it
    if instance.layerset2:
        if instance.layerset2.layer_set.all().count() == 0:
            instance.layerset2.delete()
