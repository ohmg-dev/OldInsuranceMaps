import logging

from django.db.models import signals
from django.dispatch import receiver

from geonode.layers.models import Style
from geonode.thumbs.thumbnails import create_thumbnail

from georeference.models import (
    GCPGroup,
    PrepSession,
    GeorefSession,
    TrimSession,
    LayerMask,
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

    if instance.stage == "input":
        logger.info(f"{instance.__str__()} | delete and set document {instance.document.pk} - 'unprepared'")
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

    if instance.stage == "input":
        tkm = TKeywordManager()
        if GCPGroup.objects.filter(document=instance.document).exists():
            new_status = "georeferenced"
        else:
            new_status = "prepared"
        logger.info(f"{instance.__str__()} | delete and set document {instance.document.pk} - '{new_status}'")
        tkm.set_status(instance.document, new_status)

@receiver(signals.pre_delete, sender=TrimSession)
def pre_delete_trimsession(sender, instance, **kwargs):
    """
    Emulate a cancellation of sessions that have not yet been run, i.e. are in
    the input stage.
    
    If a LayerMask exists, assume the layer has been trimmed through 
    a past session, and reset status to 'trimmed'.
    
    Otherwise, reset to 'georeferenced'.
    """

    if instance.stage == "input":
        tkm = TKeywordManager()
        if LayerMask.objects.filter(layer=instance.layer).exists():
            new_status = "georeferenced"
        else:
            new_status = "prepared"
        logger.info(f"{instance.__str__()} | delete and set document {instance.document.pk} - '{new_status}'")
        tkm.set_status(instance.document, new_status)

@receiver(signals.pre_delete, sender=LayerMask)
def pre_delete_layer_mask(sender, instance, **kwargs):

    # delete the existing trim style in Geoserver if necessary
    cat = get_gs_catalog()
    trim_style_name = f"{instance.layer.name}_trim"
    gs_trim_style = cat.get_style(trim_style_name, workspace="geonode")
    if gs_trim_style is not None:
        cat.delete(gs_trim_style, recurse=True)

    # delete the existing trimmed style in GeoNode
    Style.objects.filter(name=trim_style_name).delete()

    # set the full style back to the default in GeoNode
    gn_full_style = Style.objects.get(name=instance.layer.name)
    instance.layer.default_style = gn_full_style
    instance.layer.save()

    # update thumbnail
    thumb = create_thumbnail(instance.layer, overwrite=True)
    instance.layer.thumbnail_url = thumb
    instance.layer.save()

    # set all existing TrimSessions for the layer as "unapplied"
    for ts in TrimSession.objects.filter(layer=instance.layer):
        ts.update_status("unapplied")
    # set layer status to 'georeferenced'
    tkm = TKeywordManager()
    tkm.set_status(instance.layer, "georeferenced")
