'''
This is a step toward moving database models from the loc_insurancemaps app into
this content app. At present, these are not Django models or even Django proxy models,
just light-weight objects that are instantiated through the Volume and related
models. This will allow the codebase to slowly evolve before actually changing any
database content and running migrations.

The eventual migration plan is this:

ohmg.loc_insurancemaps.models.Volume        --> content.models.Map
ohmg.loc_insurancemaps.models.Sheet         --> content.models.Resource

new model (idea)                            --> content.models.ItemConfigPreset
    This would allow an extraction of Sanborn-specific properties vs. generic item
    uploads. Still unclear exactly what to call this, or everything that it would have.
    Think about this more when the Map model is created, and a hard-look is made at its
    attributes.
'''

import os
import logging
from datetime import datetime

from django.core.files import File
from django.core.files.base import ContentFile
from django.contrib.gis.db import models

from ohmg.utils import slugify
from ohmg.loc_insurancemaps.utils import (
    get_jpg_from_jp2_url,
)
from ohmg.georeference.storage import OverwriteStorage
from ohmg.georeference.renderers import generate_document_thumbnail_content
from ohmg.loc_insurancemaps.models import Volume

logger = logging.getLogger(__name__)


class Map(object):

    pass


class Resource(object):
    """Resources represent the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    page_number = models.CharField(max_length=10, null=True, blank=True)
    file = models.FileField(
        upload_to='resources',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    thumbnail = models.FileField(
        upload_to='thumbnails',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    source_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Storing a source_url allows this resource to be downloaded at any point after "\
            "the instance has been created."
    )
    load_date = models.DateTimeField(null=True, blank=True)

    @property
    def name(self):
        return f"{self.volume.__str__()} p{self.page_number}"

    def __str__(self):
        return self.name
    
    def download_file(self):

        log_prefix = f"{self.__str__()} |"
        logger.info(f"{log_prefix} start load")

        if not self.source_url:
            logger.warn(f"{log_prefix} no source_url - cancelling download")
            return

        if not self.file:
            jpg_path = get_jpg_from_jp2_url(self.source_url)
            with open(jpg_path, "rb") as new_file:
                self.file.save(f"{slugify(self.name)}.jpg", File(new_file))
            os.remove(jpg_path)

        self.load_date = datetime.now()
        self.save()

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_document_thumbnail_content(path)
            tname = f"{name}-res-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))
