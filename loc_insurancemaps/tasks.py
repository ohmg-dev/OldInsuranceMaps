"""
DEPRECATED
the MapCollectionItem and MapScan models are no longer in use. currently the
tasks below are only called in the old_models.py file (i.e. they are not in use).
"""

import os
from os import access, R_OK
from os.path import isfile

from django.contrib.auth import get_user_model

from celery import shared_task
from celery.utils.log import get_task_logger

from .renderers import (
    generate_collection_item_thumbnail_content,
    get_image_content_from_url,
    generate_loc_document_thumbnail
)
# from .models import MapCollectionItem, MapScan
from .models import Volume

logger = get_task_logger(__name__)

@shared_task
def import_sheets_as_task(volume_id, userid):

    user = get_user_model().objects.get(pk=userid)
    logger.debug(user.username)
    volume = Volume.objects.get(pk=volume_id)
    volume.import_sheets(user=user)

@shared_task
def create_document_thumbnail(document_id):
    generate_loc_document_thumbnail(document_id)



# @app.task(bind=True, queue='update')
def create_collection_item_thumbnail(self, object_id):
    """
    Create thumbnail for a document.
    """
    logger.debug("Generating thumbnail for collection item #{}.".format(object_id))

    try:
        item = MapCollectionItem.objects.get(id=object_id)
    except MapCollectionItem.DoesNotExist:
        logger.error("Collection Item #{} does not exist.".format(object_id))
        return

    image_path = item.doc_file.path
    try:
        if image_path:
            assert isfile(image_path) and access(image_path, R_OK) and os.stat(image_path).st_size > 0
    except (AssertionError, TypeError) as e:
        image_path = None

    if not image_path:
        image_path = item.find_placeholder()
    if not image_path or not os.path.exists(image_path):
        logger.debug("Could not find placeholder for document #{}"
                     .format(object_id))
        return

    thumbnail_content = None
    thumbnail_content = generate_collection_item_thumbnail_content(image_path,
        number=item.file_count)
    # print(thumbnail_content)
    if not thumbnail_content:
        logger.warning("Thumbnail for document #{} empty.".format(object_id))
    filename = 'document-{}-thumb.png'.format(item.uuid)
    item.save_thumbnail(filename, thumbnail_content)
    logger.debug("Thumbnail for document #{} created.".format(object_id))

# @app.task(bind=True, queue='update')
def create_map_sheet_thumbnail(self, object_id):
    """
    Create thumbnail for a document.
    """
    logger.debug("Generating thumbnail for map sheet #{}.".format(object_id))

    try:
        item = MapScan.objects.get(id=object_id)
    except MapScan.DoesNotExist:
        logger.error("Collection Item #{} does not exist.".format(object_id))
        return

    ## this could be run from the file path too, and will need to be for
    ## chopped inset pieces.
    # image_path = item.doc_file.path
    # try:
    #     if image_path:
    #         assert isfile(image_path) and access(image_path, R_OK) and os.stat(image_path).st_size > 0
    # except (AssertionError, TypeError) as e:
    #     image_path = None
    #
    # if not image_path:
    #     image_path = item.find_placeholder()
    # if not image_path or not os.path.exists(image_path):
    #     logger.debug("Could not find placeholder for document #{}"
    #                  .format(object_id))
    #     return

    thumbnail_content = None
    if item.iiif_service is not None:
        thumb_url = item.iiif_service + "/full/pct:2.5/0/default.jpg"
        thumbnail_content = get_image_content_from_url(thumb_url)

    if not thumbnail_content:
        logger.warning("Thumbnail for document #{} empty.".format(object_id))
    filename = 'document-{}-thumb.png'.format(item.uuid)
    item.save_thumbnail(filename, thumbnail_content)
    logger.debug("Thumbnail for document #{} created.".format(object_id))
