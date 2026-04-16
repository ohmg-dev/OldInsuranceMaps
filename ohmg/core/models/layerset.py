import logging
import urllib.parse
from typing import TYPE_CHECKING, Iterable, Union

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.contrib.postgres.fields import ArrayField
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from ..storages import get_file_url

if TYPE_CHECKING:
    from .layer import Layer
# from .map import Map

logger = logging.getLogger(__name__)


class LayerSetCategory(models.Model):
    class Meta:
        verbose_name_plural = "Layer Set Categories"

    slug = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    display_name = models.CharField(max_length=50)

    def __str__(self):
        return self.display_name if self.display_name else self.slug


class LayerSet(models.Model):
    class Meta:
        verbose_name_plural = "Layer Sets"

    map = models.ForeignKey(
        "core.Map",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        LayerSetCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    mosaic_geotiff = models.FileField(
        upload_to="mosaics",
        null=True,
        blank=True,
        max_length=255,
    )
    mosaic_json = models.FileField(
        upload_to="mosaics",
        null=True,
        blank=True,
        max_length=255,
    )
    extent = ArrayField(
        models.FloatField(),
        size=4,
        null=True,
        blank=True,
    )
    tilejson = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.map} - {self.category}"

    def layer_display_list(self):
        """For display in the admin interface only."""
        li = [
            f"<li><a href='/admin/core/layer/{i.pk}/change'>{i}</a></li>" for i in self.get_layers()
        ]
        return mark_safe("<ul>" + "".join(li) + "</ul>")

    layer_display_list.short_description = "Layers"

    def get_layers(self) -> Iterable["Layer"]:
        return self.layer_set.all()

    @cached_property
    def centroid(self):
        return Polygon.from_bbox(self.extent).centroid

    @property
    def mosaic_cog_url(self):
        """return the public url to the mosaic COG for this annotation set. If
        no COG exists, return None."""
        return get_file_url(self, "mosaic_geotiff")

    @cached_property
    def file_url_encoded(self):
        """return the public url to the mosaic COG for this annotation set. If
        no COG exists, return None."""
        return urllib.parse.quote(self.mosaic_cog_url, safe="")

    def create_xyz_url(self) -> Union[str, None]:
        file_url = get_file_url(self, "mosaic_geotiff")
        if file_url:
            encoded_url = urllib.parse.quote(file_url, safe="")
            xyx_base = (
                f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@2x.png?"
            )
            return f"{xyx_base}&url={encoded_url}"
        else:
            return None

    @property
    def multimask_extent(self):
        """Calculate an extent based any existing masks of layers in this LayerSet.
        If no layer have masks then return None."""
        feature_polygons = []
        for feat in self.multimask_geojson["features"]:
            poly = Polygon(feat["geometry"]["coordinates"][0])
            feature_polygons.append(poly)
        return (
            MultiPolygon(feature_polygons, srid=4326).extent if len(feature_polygons) > 0 else None
        )

    @property
    def multimask_geojson(self) -> dict:
        """Collect all masks from layers in this layerset and return as GeoJSON Feature Collection"""
        fc = {"type": "FeatureCollection", "features": []}
        for layer in self.get_layers():
            mask_geojson = layer.mask_geojson_feature
            if mask_geojson:
                fc["features"].append(mask_geojson)
        return fc

    def save(self, set_tilejson: bool = False, *args, **kwargs):
        if self._state.adding is False:
            extents = self.get_layers().values_list("extent", flat=True)
            layer_extents = []
            for extent in extents:
                if extent:
                    poly = Polygon().from_bbox(extent)
                    layer_extents.append(poly)
            if layer_extents:
                combined = MultiPolygon(layer_extents)
                self.extent = combined.extent
            if (set_tilejson or self.tilejson is None) and self.mosaic_geotiff:
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
