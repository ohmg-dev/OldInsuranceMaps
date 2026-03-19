import json
import logging
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Union

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon
from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils.functional import cached_property

from ..storages import get_file_url
from ..utils import (
    get_session_user_summary,
    slugify,
)
from ..utils.image import (
    generate_layer_thumbnail_content,
    get_extent_from_file,
)

if TYPE_CHECKING:
    from .map import Map

logger = logging.getLogger(__name__)


class Layer(models.Model):
    class Meta:
        verbose_name_plural = " Layers"

    title = models.CharField(max_length=200, default="untitled layer")
    nickname = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=100)
    region = models.OneToOneField(
        "core.Region",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="layers_created",
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="layers_updated",
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    extent = ArrayField(
        models.FloatField(),
        size=4,
        null=True,
        blank=True,
    )
    mask = models.PolygonField(blank=True, null=True)
    file = models.FileField(
        upload_to="layers",
        null=True,
        blank=True,
        max_length=255,
    )
    thumbnail = models.FileField(
        upload_to="thumbnails",
        null=True,
        blank=True,
        max_length=255,
    )
    layerset2 = models.ForeignKey(
        "core.LayerSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tilejson = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.title

    @cached_property
    def map(self) -> "Map":
        return self.region.document.map

    @cached_property
    def centroid(self):
        return Polygon.from_bbox(self.extent).centroid

    @cached_property
    def file_url(self):
        return get_file_url(self)

    @cached_property
    def file_url_encoded(self):
        """return the public url to the mosaic COG for this annotation set. If
        no COG exists, return None."""
        return urllib.parse.quote(self.file_url, safe="")

    @property
    def mask_geojson_feature(self) -> Union[dict | None]:
        """Returns a GeoJSON feature representation of the Layer mask, or None if no mask"""
        return (
            {
                "type": "Feature",
                "geometry": json.loads(self.mask.geojson),
                "properties": {"layer": self.slug},
            }
            if self.mask
            else None
        )

    def create_xyz_url(self) -> Union[str, None]:
        file_url = get_file_url(self)
        if file_url:
            encoded_url = urllib.parse.quote(file_url, safe="")
            xyx_base = (
                f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@2x.png?"
            )
            return f"{xyx_base}&url={encoded_url}"
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
            content = generate_layer_thumbnail_content(self.file)
            tname = f"{Path(self.file.url).stem}-lyr-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def set_layerset(self, layerset):
        from .layerset import LayerSet

        # if it's the same LayerSet then do nothing
        if self.layerset2 == layerset:
            logger.debug(
                f"Layer {self.pk} already in LayerSet {layerset} ({layerset.pk}), no action"
            )
            return

        # make sure to clean up the existing multimask in the current vrs if necessary
        existing_obj = LayerSet.objects.get(pk=self.layerset2.pk) if self.layerset2 else None
        delete_existing = existing_obj and existing_obj.get_layers().count() == 1
        self.layerset2 = layerset
        self.save(update_fields=["layerset2"])
        logger.info(f"Layer {self.pk} added to LayerSet {self.layerset2} ({self.layerset2.pk})")

        if delete_existing:
            msg = f"Emptied LayerSet {existing_obj} ({existing_obj.pk}) deleted"
            existing_obj.delete()
            logger.info(msg)

        # little patch in here to make sure the new Map objects get added to the layerset,
        # before everything is shifted away from the Volume model
        if not layerset.map:
            layerset.map = self.region.document.map

        # save here to trigger a recalculation of the layerset's extent
        layerset.save()

    def get_creators(self):
        from ohmg.georeference.models import SessionBase

        sessions = SessionBase.objects.filter(Q(doc2=self.region.document) | Q(reg2=self.region))
        user_list = get_session_user_summary(sessions)
        return [
            {
                "id": f"https://oldinsurancemaps.net/profile/{i['name']}",
                "type": "Person",
            }
            for i in user_list
        ]

    def save(
        self,
        set_slug: bool = False,
        set_thumbnail: bool = False,
        set_extent: bool = True,
        set_tilejson: bool = False,
        skip_map_lookup_update: bool = False,
        *args,
        **kwargs,
    ):
        # attach this flag which is checked on the post_save signal receiver
        self.skip_map_lookup_update = skip_map_lookup_update

        if set_slug or not self.slug:
            self.slug = slugify(self.region.__str__(), join_char="_")

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_extent and self.file:
            self.extent = get_extent_from_file(self.file)

        self.title = self.region.title
        self.nickname = self.region.nickname

        if (set_tilejson or self.tilejson is None) and self.file:
            self.tilejson = {
                "tilejson": "2.2.0",
                "version": "1.0.0",
                "scheme": "xyz",
                "tiles": [self.create_xyz_url()],
                "minzoom": 10,
                "maxzoom": 21,
                "bounds": self.extent,
                "center": [self.centroid[0], self.centroid[1], 16],
                "attribution": "<a href='https://oldinsurancemaps.net'>OldInsuranceMaps</a>; <a href='https://loc.gov/collections/sanborn-maps'>LOC</a>",
            }

        return super(self.__class__, self).save(*args, **kwargs)
