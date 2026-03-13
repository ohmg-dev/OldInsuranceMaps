import logging
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from django.utils.functional import cached_property

from ..utils import (
    slugify,
)
from ..utils.image import (
    generate_document_thumbnail_content,
    get_image_size,
)

if TYPE_CHECKING:
    from .map import Map

logger = logging.getLogger(__name__)


class RegionCategory(models.Model):
    class Meta:
        verbose_name_plural = "  Region Categories"

    slug = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    display_name = models.CharField(max_length=50)

    def __str__(self):
        return self.display_name if self.display_name else self.slug


class Region(models.Model):
    class Meta:
        verbose_name_plural = "  Regions"

    title = models.CharField(max_length=200, default="untitled region")
    nickname = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=100)
    boundary = models.PolygonField(
        null=True,
        blank=True,
    )
    document = models.ForeignKey("core.Document", on_delete=models.CASCADE, related_name="regions")
    division_number = models.IntegerField(null=True, blank=True)
    is_map = models.BooleanField(default=True)
    category = models.ForeignKey(RegionCategory, on_delete=models.PROTECT, null=True, blank=True)
    georeferenced = models.BooleanField(default=False)
    skipped = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="region_created_by",
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    file = models.FileField(
        upload_to="regions",
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

    def __str__(self):
        return self.title

    @cached_property
    def map(self) -> "Map":
        return self.document.map

    @property
    def transformation(self):
        if hasattr(self, "gcpgroup"):
            return self.gcpgroup.transformation
        else:
            return None

    @property
    def gcps_geojson(self):
        if hasattr(self, "gcpgroup"):
            return self.gcpgroup.as_geojson
        else:
            return None

    @property
    def lock(self):
        from ohmg.georeference.models import SessionLock

        ct = ContentType.objects.get_for_model(self)
        locks = SessionLock.objects.filter(target_type=ct, target_id=self.pk)
        if locks.exists():
            return locks[0]
        else:
            return None

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            content = generate_document_thumbnail_content(self.file)
            tname = f"{Path(self.file.url).stem}-reg-thumb.jpg"
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
            display_name = self.document.__str__()
            if self.division_number:
                display_name += f" [{self.division_number}]"
            self.slug = slugify(display_name, join_char="_")

        self.title = self.document.title
        if self.division_number:
            self.title += f" [{self.division_number}]"

        self.nickname = self.document.nickname
        if self.division_number and self.nickname:
            self.nickname += f" [{self.division_number}]"

        if set_image_size or not self.image_size:
            self.image_size = get_image_size(self.file) if self.file else None

        return super(self.__class__, self).save(*args, **kwargs)
