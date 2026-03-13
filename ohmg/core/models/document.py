import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.files import File
from django.core.files.base import ContentFile

from ..utils import (
    slugify,
)
from ..utils.image import (
    convert_img_format,
    generate_document_thumbnail_content,
    get_image_size,
)
from ..utils.requests import download_image

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class Document(models.Model):
    """Documents are the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""

    class Meta:
        verbose_name_plural = "   Documents"

    title = models.CharField(max_length=200, default="untitled document")
    nickname = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=100)
    map = models.ForeignKey("core.Map", on_delete=models.CASCADE, related_name="documents")
    page_number = models.CharField(max_length=10, null=True, blank=True)
    prepared = models.BooleanField(default=False)
    loading_file = models.BooleanField(default=False)
    file = models.FileField(
        upload_to="documents",
        null=True,
        blank=True,
        max_length=255,
    )
    image_size = ArrayField(
        models.IntegerField(),
        size=2,
        null=True,
        blank=True,
    )
    thumbnail = models.FileField(
        upload_to="thumbnails",
        null=True,
        blank=True,
        max_length=255,
    )
    source_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Storing a source_url allows the file to be downloaded at any point after "
        "the instance has been created.",
    )
    iiif_info = models.JSONField(null=True, blank=True)
    load_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def layers(self):
        from .layer import Layer

        return Layer.objects.filter(region_id__in=self.regions.all().values_list("id", flat=True))

    @property
    def lock(self):
        from ohmg.georeference.models import SessionLock

        ct = ContentType.objects.get_for_model(self)
        locks = SessionLock.objects.filter(target_type=ct, target_id=self.pk)
        if locks.exists():
            return locks[0]
        else:
            return None

    def load_file_from_source(self, username, overwrite=False):
        log_prefix = f"{self.__str__()} |"
        logger.info(f"{log_prefix} start load")
        self.loading_file = True
        self.save()

        if self.source_url:
            src_url = self.source_url
        elif self.iiif_info:
            src_url = self.iiif_info.replace("info.json", "full/full/0/default.jpg")
        elif self.source_url:
            src_url = self.source_url
        else:
            logger.warning(f"{log_prefix} no source_url or iiif_info - cancelling download")
            return

        if self.file != "" and not overwrite:
            logger.warning(f"{log_prefix} won't overwrite existing file")
            return

        src_path = Path(src_url)
        tmp_img_dir = Path(settings.CACHE_DIR, "images")
        tmp_img_dir.mkdir(exist_ok=True, parents=True)
        tmp_path = Path(tmp_img_dir, src_path.name)

        if src_url.startswith("http"):
            out_file = download_image(src_url, tmp_path, use_cache=not overwrite)
            if out_file is None:
                logger.error(f"can't get {src_url} -- skipping")
                return
        else:
            if not tmp_path.exists():
                shutil.copyfile(src_path, tmp_path)

        if not src_url.endswith(".jpg"):
            tmp_path = convert_img_format(tmp_path, force=True)

        if not tmp_path.exists():
            logger.error(f"{log_prefix} can't retrieve source: {src_url}. Moving to next Document.")
            return

        with open(tmp_path, "rb") as new_file:
            self.file.save(f"{self.slug}{tmp_path.suffix}", File(new_file))

        self.load_date = datetime.now()
        self.loading_file = False
        if self.map.loaded_by is None:
            self.map.loaded_by = get_user_model().objects.get(username=username)
            self.map.load_date = self.load_date
            self.map.save(update_fields=["loaded_by", "load_date"])
        self.save(set_thumbnail=True)

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            content = generate_document_thumbnail_content(self.file)
            tname = f"{Path(self.file.url).stem}-doc-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def save(
        self,
        set_slug: bool = False,
        set_thumbnail: bool = False,
        set_image_size: bool = False,
        skip_map_lookup_update: bool = False,
        *args,
        **kwargs,
    ):
        # attach this flag which is checked on the post_save signal receiver
        self.skip_map_lookup_update = skip_map_lookup_update

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_slug or not self.slug:
            title = self.map.__str__()
            if self.page_number:
                title += f" {self.map.DOCUMENT_PREFIX_ABBREVIATIONS[self.map.document_page_type]}{self.page_number}"
            self.slug = slugify(title, join_char="_")

        self.title = self.map.title
        if self.page_number:
            self.title += f" {self.map.DOCUMENT_PREFIX_ABBREVIATIONS[self.map.document_page_type]}{self.page_number}"

        self.nickname = self.map.title
        if self.page_number and self.nickname:
            self.nickname = f"{self.map.document_page_type} {self.page_number}"

        if set_image_size or not self.image_size:
            self.image_size = get_image_size(self.file) if self.file else None

        if self._state.adding is False:
            self.prepared = self.regions.all().count() > 0

        return super(self.__class__, self).save(*args, **kwargs)
