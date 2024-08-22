import os
import logging
from typing import Union
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.utils import timezone
from django.contrib.gis.geos import Polygon

from ohmg.core.models import Document, Region, Layer
from ohmg.core.utils import random_alnum, save_file_to_object
from ..georeferencer import Georeferencer
from ..splitter import Splitter
from ..models import GeorefSession, PrepSession, GCPGroup

logger = logging.getLogger(__name__)

def generate_vrt_from_session(session: Union[int, GeorefSession]):

    if isinstance(session, int):
        session = GeorefSession.objects.get(pk=session)

    crs_code = f"EPSG:{session.data['epsg']}"
    g = Georeferencer(
        crs=crs_code,
        transformation=session.data['transformation'],
        gcps_geojson=session.data['gcps'],
    )
    vrt_path = g.warp(session.reg2.file.path, return_vrt=True)
    return vrt_path

def run_georeferencing(session: Union[int, GeorefSession]):

    logger.debug("in run_georef_session()")

    if isinstance(session, int):
        session = GeorefSession.objects.get(pk=session)

    existing_file_path = None

    layer = None
    if hasattr(session.reg2, 'layer'):
        layer = session.reg2.layer

    session.date_run = timezone.now()
    # first time the session is run, calculate the user input time (seconds)
    if session.user_input_duration is None:
        timediff = timezone.now() - session.date_created
        session.user_input_duration = timediff.seconds

    session.update_stage("processing", save=False)
    session.update_status("initializing georeferencer", save=False)
    session.save()

    try:
        # assume EPSG code for now, as making this completely
        # flexible is still in-development. see views.py line 277
        crs_code = f"EPSG:{session.data['epsg']}"
        g = Georeferencer(
            crs=crs_code,
            transformation=session.data['transformation'],
            gcps_geojson=session.data['gcps'],
        )
    except Exception as e:
        session.update_stage("finished", save=False)
        session.update_status("failed", save=False)
        session.note = f"{e}"
        session.save()

        session.unlock_resources2()
        return None

    session.update_status("warping")
    try:
        out_path = g.warp(session.reg2.file.path)
    except Exception as e:
        logger.error(e)
        session.update_stage("finished", save=False)
        session.update_status("failed", save=False)
        session.note = f"{e}"
        session.save()
        return None

    session.update_status("creating layer")

    ## if there was no existing layer, create a new object by copying
    ## the document and saving it without a pk
    if layer is None:
        logger.debug("no existing layer, creating new layer now")

        layer = Layer.objects.create(
            created_by=session.user,
            last_updated_by=session.user,
            region=session.reg2,
        )
        layer.save()

        existing_file_path = None
    else:
        logger.debug(f"updating existing layer, {layer} ({layer.pk})")
        existing_file_path = layer.file.path if layer.file else None

    ## regardless of whether there was an old layer or not, overwrite
    ## the file with the newly georeferenced tif.
    session_ct = GeorefSession.objects.filter(reg2=session.reg2).exclude(pk=session.pk).count()
    file_name = f"{layer.slug}__{random_alnum(6)}_{str(session_ct).zfill(2)}.tif"
    # file_name = f"{layer.slug}.tif"
    with open(out_path, "rb") as openf:
        layer.file.save(file_name, File(openf))
    logger.debug(f"new geotiff saved to layer, {layer.slug} ({layer.pk})")

    # remove now-obsolete tif files
    os.remove(out_path)
    if existing_file_path:
        os.remove(existing_file_path)

    layer.save(set_thumbnail=True, set_extent=True)
    session.lyr2 = layer

    # add the layer to the main-content LayerSet
    layer.layerset = layer.region.document.map.get_layerset('main-content', create=True)
    layer.save()

    session.update_status("saving control points")

    # save the successful gcps to the canonical GCPGroup for the document
    GCPGroup().save_from_geojson(
        session.data['gcps'],
        session.doc,
        session.data['transformation'],
    )

    session.doc.set_status("georeferenced")
    session.update_stage("finished", save=False)
    session.update_status("success", save=False)
    session.save()

    session.unlock_resources2()

    processing_time = timezone.now() - session.date_run
    session.send_email_notification(
        f"✔️ Georeferenced: {session.lyr2}",
        f"""Georeferencing completed for {session.lyr2}.
• session id: {session.pk}
• user: {session.user.username}
• result: {session.note}
• user input duration: {session.user_input_duration}
• processing time: {processing_time.seconds}
"""
    )

    return layer

def run_preparation(session: Union[int, PrepSession]):

    """
    Runs the document split process based on prestored segmentation info
    that has been generated for this document. New Documents are made for
    each child image, DocumentLinks are created to link this parent
    Document with its children.
    """

    session.date_run = timezone.now()
    # first time the session is run, calculate the user input time (seconds)
    if session.user_input_duration is None:
        timediff = timezone.now() - session.date_created
        session.user_input_duration = timediff.seconds

    session.update_stage("processing")

    if session.data['split_needed'] is False:
        # create Region that matches this document
        w, h = session.doc2.image_size
        region = Region.objects.create(
            boundary = Polygon([[0,0], [0,h], [w,h], [w,0], [0,0]]),
            document=session.doc2,
            created_by=session.user,
        )
        save_file_to_object(region, source_object=session.doc2)

    else:
        session.update_status("splitting document image")
        s = Splitter(image_file=session.doc2.file.path)
        session.data['divisions'] = s.generate_divisions(session.data['cutlines'])
        new_images = s.split_image()

        for div_no, file_path in enumerate(new_images, start=1):
            session.update_status(f"creating new region [{div_no}]")
            
            # get division by index in the original list that was passed to the splitter
            # would be better to have these returned with the new_images, ultimately
            div = session.data['divisions'][div_no-1]
            div_polygon = Polygon(div)
            region = Region.objects.create(
                boundary = div_polygon,
                document=session.doc2,
                division_number=div_no,
                created_by=session.user,
            )

            save_file_to_object(region, file_path=Path(file_path))
            os.remove(file_path)

    session.update_status("success", save=False)
    session.update_stage("finished", save=False)
    session.save()

    session.unlock_resources2()

    processing_time = timezone.now() - session.date_run
    session.send_email_notification(
        f"✔️ Prepared: {session.doc2}",
        f""""Preparation completed for {session.doc2}.
• session id: {session.pk}
• user: {session.user.username}
• result: {session.note}
• user input duration: {session.user_input_duration}
• processing time: {processing_time.seconds}
"""
    )

    return
