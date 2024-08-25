import os
import glob
import uuid
import json
import logging
from datetime import timedelta, datetime
from osgeo import gdal, osr
from PIL import Image
from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.gis.geos import Point, Polygon, MultiPolygon, GEOSGeometry
from django.contrib.gis.db import models
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from cogeo_mosaic.mosaic import MosaicJSON
from cogeo_mosaic.backends import MosaicBackend

from ohmg.core.utils import (
    full_reverse,
    slugify,
    random_alnum,
)
from ohmg.core.renderers import generate_document_thumbnail_content, generate_layer_thumbnail_content
from ohmg.georeference.storage import OverwriteStorage

logger = logging.getLogger(__name__)

class GCP(models.Model):

    class Meta:
        verbose_name = "GCP"
        verbose_name_plural = "GCPs"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pixel_x = models.IntegerField(null=True, blank=True)
    pixel_y = models.IntegerField(null=True, blank=True)
    geom = models.PointField(null=True, blank=True, srid=4326)
    note = models.CharField(null=True, blank=True, max_length=255)
    gcp_group = models.ForeignKey(
        "GCPGroup",
        on_delete=models.CASCADE)

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        null=False,
        blank=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name='created_by',
        on_delete=models.CASCADE)
    last_modified = models.DateTimeField(
        auto_now=True,
        editable=False,
        null=False,
        blank=False)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name='modified_by',
        on_delete=models.CASCADE)


class GCPGroup(models.Model):

    TRANSFORMATION_CHOICES = (
        ("tps", "tps"),
        ("poly1", "poly1"),
        ("poly2", "poly2"),
        ("poly3", "poly3"),
    )

    class Meta:
        verbose_name = "GCP Group"
        verbose_name_plural = "GCP Groups"

    doc = models.ForeignKey(
        "Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    crs_epsg = models.IntegerField(null=True, blank=True)
    transformation = models.CharField(
        null=True,
        blank=True,
        choices=TRANSFORMATION_CHOICES,
        max_length=20,
    )

    def __str__(self):
        if self.doc:
            return self.doc.title
        else:
            return str(self.pk)

    @property
    def gcps(self):
        return GCP.objects.filter(gcp_group=self)

    @property
    def gdal_gcps(self):
        gcp_list = []
        for gcp in self.gcps:
            geom = gcp.geom.clone()
            geom.transform(self.crs_epsg)
            p = gdal.GCP(geom.x, geom.y, 0, gcp.pixel_x, gcp.pixel_y)
            gcp_list.append(p)
        return gcp_list

    @property
    def as_geojson(self):

        geo_json = {
          "type": "FeatureCollection",
          "features": []
        }

        for gcp in self.gcps:
            coords = json.loads(gcp.geom.geojson)["coordinates"]
            newcoords = [coords[1], coords[0]]
            # see note on this variable in settings.py
            if settings.SWAP_COORDINATE_ORDER is True:
                newcoords = coords
            geo_json['features'].append({
                "type": "Feature",
                "properties": {
                  "id": str(gcp.pk),
                  "image": [gcp.pixel_x, gcp.pixel_y],
                  "username": gcp.last_modified_by.username,
                  "note": gcp.note,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": newcoords,
                }
            })
        return geo_json

    def as_points_file(self):

        content = "mapX,mapY,pixelX,pixelY,enable\n"
        for gcp in self.gcps:
            geom = gcp.geom.clone()
            geom.transform(self.crs_epsg)
            # pixel_y must be inverted b/c qgis puts origin at top left corner
            content += f"{geom.x},{geom.y},{gcp.pixel_x},-{gcp.pixel_y},1\n"

        return content

    def save_from_geojson(self, geojson, document, transformation=None):

        group, group_created = GCPGroup.objects.get_or_create(doc=document)

        group.crs_epsg = 3857 # don't see this changing any time soon...
        group.transformation = transformation
        group.save()

        gcps_new, gcps_mod, gcps_del = 0, 0, 0

        # first remove any existing gcps that have been deleted
        for gcp in group.gcps:
            if str(gcp.id) not in [i['properties'].get('id') for i in geojson['features']]:
                gcps_del += 0
                gcp.delete()

        for feature in geojson['features']:

            id = feature['properties'].get('id', str(uuid.uuid4()))
            username = feature['properties'].get('username')
            user = get_user_model().objects.get(username=username)
            gcp, created = GCP.objects.get_or_create(
                id = id,
                defaults = {
                    'gcp_group': group,
                    'created_by': user
                })
            if created:
                gcps_new += 1

            pixel_x = feature['properties']['image'][0]
            pixel_y = feature['properties']['image'][1]
            new_pixel = (pixel_x, pixel_y)
            old_pixel = (gcp.pixel_x, gcp.pixel_y)
            lng = feature['geometry']['coordinates'][0]
            lat = feature['geometry']['coordinates'][1]

            new_geom = Point(lat, lng, srid=4326)

            # only update the point if one of its coordinate pairs have changed,
            # this also triggered when new GCPs have None for pixels and geom.
            if new_pixel != old_pixel or not new_geom.equals(gcp.geom) or gcp.note != feature['properties']['note']:
                gcp.note = feature['properties']['note']
                gcp.pixel_x = new_pixel[0]
                gcp.pixel_y = new_pixel[1]
                gcp.geom = new_geom
                gcp.last_modified_by = user
                gcp.save()
                if not created:
                    gcps_mod += 1
        gcps_ct = len(geojson['features'])
        logger.info(f"GCPGroup {group.pk} | GCPs ct: {gcps_ct}, new: {gcps_new}, mod: {gcps_mod}, del: {gcps_del}")
        return group

    def save_from_annotation(self, annotation, document):

        m = "georeference-ground-control-points"
        georef_annos = [i for i in annotation['items'] if i['motivation'] == m]
        anno = georef_annos[0]

        self.save_from_geojson(anno['body'], document, "poly1")


class DocumentManager(models.Manager):

    _type = 'document'

    def get_queryset(self):
        return super(DocumentManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
        })
        return super(DocumentManager, self).create(**kwargs)


class LayerManager(models.Manager):

    _type = 'layer'

    def get_queryset(self):
        return super(LayerManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
        })
        return super(LayerManager, self).create(**kwargs)

def set_upload_location(instance, filename):
    """ this function has to return the location to upload the file """
    return os.path.join(f"{instance.type}s", filename)

class ItemBase(models.Model):

    GEOREF_STATUS_CHOICES = (
        ("unprepared", "Unprepared"),
        ("needs review", "Needs Review"),
        ("splitting", "Splitting - in progress"),
        ("split", "Split"),
        ("prepared", "Prepared"),
        ("georeferencing", "Georeferencing - in progress"),
        ("georeferenced", "Georeferenced"),
        ("nonmap", "Non-Map"),
    )

    title = models.CharField('title', max_length=255)
    slug = models.CharField(
        max_length=128, null=True, blank=True
    )
    type = models.CharField(
        max_length=10,
        choices=(("document", "Document"), ("layer", "Layer")),
    )
    date = models.DateTimeField(
        default=timezone.now
    )
    attribution = models.CharField(
        max_length=2048,
        blank=True,
        null=True,
    )
    status = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        default=GEOREF_STATUS_CHOICES[0][0],
        choices=GEOREF_STATUS_CHOICES
    )

    x0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True
    )
    y0 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True
    )
    x1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True
    )
    y1 = models.DecimalField(
        max_digits=30,
        decimal_places=15,
        blank=True,
        null=True
    )

    epsg = models.IntegerField(
        blank=True,
        null=True,
    )

    favorite_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    file = models.FileField(
        upload_to=set_upload_location,
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
    lock_enabled = models.BooleanField(
        default=False,
    )
    lock_details = models.JSONField(
        null=True,
        blank=True,
    )
    vrs = models.ForeignKey(
        "georeference.LayerSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return str(self.title)

    @property
    def _base_urls(self):
        return {
            "thumbnail": self.thumbnail.url if self.thumbnail else "",
            "image": self.file.url if self.file else "",
        }

    @property
    def bbox(self):
        """BBOX is in the format: [x0, x1, y0, y1, srid]."""
        if self.extent:
            xmin, ymin, xmax, ymax = self.extent
            return [xmin, xmax, ymin, ymax, "EPSG:4326"]
        else:
            return [-180, 180, -90, 90, "EPSG:4326"]

    @property
    def extent(self):
        """ returns an extent tuple """
        extent = None
        if self.x0 is not None:
            extent = (
                float(self.x0),
                float(self.y0),
                float(self.x1),
                float(self.y1)
            )
        return extent

    def add_lock(self, session):
        expiration = timezone.now() + timedelta(seconds=settings.GEOREFERENCE_SESSION_LENGTH)
        lock_details = {
            'session_type': session.type,
            'session_id': session.pk,
            'user': {
                "name": session.user.username,
                "profile": full_reverse("profile_detail", args=(session.user.username, )),
            },
            'expiration': expiration.timestamp()
        }
        self.lock_details = lock_details
        self.lock_enabled = True
        self.save(update_fields=["lock_details", "lock_enabled"])

    def remove_lock(self):
        self.lock_details = None
        self.lock_enabled = False
        self.save(update_fields=["lock_details", "lock_enabled"])

    def extend_lock(self):
        if self.lock_enabled:
            expiration = datetime.fromtimestamp(self.lock_details['expiration'])
            new_dt = expiration + timedelta(seconds=settings.GEOREFERENCE_SESSION_LENGTH)
            self.lock_details['expiration'] = new_dt.timestamp()
            self.save(update_fields=["lock_details", "lock_enabled"])
        else:
            logger.warn(f"{self.type} resource ({self.pk}): no existing lock to extend.")

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            if self.type == "document":
                content = generate_document_thumbnail_content(path)
                tname = f"{name}-doc-thumb.jpg"
            elif self.type == "layer":
                content = generate_layer_thumbnail_content(path)
                tname = f"{name}-lyr-thumb.jpg"
            else:
                return None
            self.thumbnail.save(tname, ContentFile(content))

    def set_extent(self):
        """ https://gis.stackexchange.com/a/201320/28414 """
        if self.file is not None:
            src = gdal.Open(self.file.path)
            ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
            lrx = ulx + (src.RasterXSize * xres)
            lry = uly + (src.RasterYSize * yres)

            src = None
            del src

            webMerc = osr.SpatialReference()
            webMerc.ImportFromEPSG(3857)
            wgs84 = osr.SpatialReference()
            wgs84.ImportFromEPSG(4326)
            transform = osr.CoordinateTransformation(webMerc, wgs84)

            ul = transform.TransformPoint(ulx, uly)
            lr = transform.TransformPoint(lrx, lry)

            self.x0 = ul[1]
            self.y0 = lr[0]
            self.x1 = lr[1]
            self.y1 = ul[0]

    def set_status(self, status, save=True):
        self.status = status
        if save is True:
            self.save(update_fields=["status"])

    def update_annotationset(self, vrs):

        # if it's the same vrs then do nothing
        if self.vrs == vrs:
            logger.debug(f"{self.pk} same as existing vrs, no action")
            return

        # make sure to clean up the existing multimask in the current vrs if necessary
        if self.vrs:
            if self.vrs.multimask and self.slug in self.vrs.multimask:
                del self.vrs.multimask[self.slug]
                self.vrs.save(update_fields=["multimask"])
                logger.warn(f"{self.pk} removed layer from existing multimask in vrs {self.vrs.pk}")
        self.vrs = vrs
        self.save(update_fields=["vrs"])
        logger.info(f"{self.pk} added to vrs {self.vrs.pk}")

    def save(self, set_slug=False, set_thumbnail=False, set_extent=False, *args, **kwargs):

        if set_slug or not self.slug:
            self.slug = slugify(self.title, join_char="_")

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_extent or (self.type == "layer" and self.file and not self.x0):
            self.set_extent()

        return super(ItemBase, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # this works because the target_id will always be pointing to an ItemBase id,
        # even though the target_type field will be a Layer or Document ContentType
        DocumentLink.objects.filter(target_id=self.pk).delete()
        return super(ItemBase, self).delete(*args, **kwargs)

class Document(ItemBase):

    objects = DocumentManager()

    class Meta:
        proxy = True
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    @cached_property
    def image_size(self):
        size = None
        if self.file:
            try:
                img = Image.open(self.file)
                size = img.size
                img.close()
            except Exception as e:
                logger.warn(f"error opening file {self.file}: {e}")
        return size

    @property
    def urls(self):
        urls = self._base_urls
        urls.update({
            "resource": full_reverse("resource_detail", args=(self.pk, )),
            # # remove detail and progress_page urls once InfoPanel has been fully
            # # deprecated and volume summary has been updated.
            # "detail": f"/documents/{self.pk}",
            # "progress_page": f"/documents/{self.pk}#georeference",
            "split": full_reverse("split_view", args=(self.pk, )),
            "georeference": full_reverse("georeference_view", args=(self.pk, )),
        })
        return urls

    @property
    def preparation_session(self):
        from ohmg.georeference.models import PrepSession
        try:
            return PrepSession.objects.get(doc=self)
        except PrepSession.DoesNotExist:
            if self.parent is not None:
                return self.parent.preparation_session
            else:
                return None
        except PrepSession.MultipleObjectsReturned:
            logger.warn(f"Multiple PrepSessions found for Document {self.id}")
            return list(PrepSession.objects.filter(doc=self))[0]

    @property
    def georeference_sessions(self):
        from ohmg.georeference.models import GeorefSession
        return GeorefSession.objects.filter(doc=self.id).order_by("date_run")

    @property
    def cutlines(self):
        cutlines = []
        if not self.parent and self.preparation_session:
            cutlines = self.preparation_session.data['cutlines']
        return cutlines

    @cached_property
    def parent(self):
        try:
            link = DocumentLink.objects.get(target_id=self.pk, link_type="split")
            parent = link.source
        except DocumentLink.DoesNotExist:
            parent = None
        return parent

    @cached_property
    def children(self):
        links = DocumentLink.objects.filter(source=self, link_type="split")
        return [i.target for i in links]

    @cached_property
    def gcp_group(self):
        try:
            return GCPGroup.objects.get(doc=self.id)
        except GCPGroup.DoesNotExist:
            return None

    @property
    def gcps_geojson(self):
        gcp_group = self.gcp_group
        if gcp_group is not None:
            return gcp_group.as_geojson
        else:
            return None

    @property
    def transformation(self):
        gcp_group = self.gcp_group
        if gcp_group is not None:
            return gcp_group.transformation
        else:
            return None

    def get_extended_urls(self):
        urls = self.urls
        urls.update(self.get_layer_urls())
        return urls

    def get_split_summary(self):

        if self.preparation_session is None:
            return None

        info = self.preparation_session.serialize()

        parent_json = None
        if self.parent:
            parent_json = self.parent.serialize(serialize_children=False)
        child_json = [i.serialize(serialize_parent=False) for i in self.children]

        info.update({
            "parent_doc": parent_json,
            "child_docs": child_json,
        })

        return info

    def get_georeference_summary(self):

        sessions = [i.serialize() for i in self.georeference_sessions]
        return {
            "sessions": sessions,
            "gcp_geojson": self.gcps_geojson,
            "transformation": self.transformation,
        }

    def get_sessions(self, serialize=False):

        ps = self.preparation_session
        if ps is not None:
            sessions = list(chain([ps], self.georeference_sessions))
            if serialize is True:
                sessions_json = [super(type(i), i).serialize() for i in sessions]
                sessions_json.sort(key=lambda i: (i['date_run'] is None, i['date_run']))
                return sessions_json
            else:
                return sessions
        else:
            return []

    def get_layer(self):
        try:
            link = DocumentLink.objects.get(link_type="georeference", source=self)
            layer = link.target
        except DocumentLink.DoesNotExist:
            layer = None
        return layer

    def serialize(self, serialize_children=True, serialize_parent=True, serialize_layer=True, include_sessions=False):

        parent = None
        if self.parent is not None:
            if serialize_parent:
                parent = self.parent.serialize(serialize_children=False, serialize_layer=serialize_layer)
            else:
                parent = self.parent.pk

        children = None
        if len(self.children) > 0:
            if serialize_children:
                children = [i.serialize(serialize_parent=False, serialize_layer=serialize_layer) for i in self.children]
            else:
                children = [i.pk for i in self.children]

        layer = self.get_layer()
        if layer is not None:
            if serialize_layer:
                layer = layer.serialize(serialize_document=False)
            else:
                layer = layer.slug

        if include_sessions is True:
            session_data = self.get_sessions(serialize=True)
        else:
            session_data = None

        return {
            "id": self.pk,
            "title": self.title,
            "type": self.type,
            "slug": self.slug,
            "status": self.status,
            "urls": self.urls,
            "image_size": self.image_size,
            "cutlines": self.cutlines,
            "parent": parent,
            "children": children,
            "layer": layer,
            "gcps_geojson": self.gcps_geojson,
            "transformation": self.transformation,
            "lock_enabled": self.lock_enabled,
            "lock_details": self.lock_details,
            "session_data": session_data,
        }

class LayerV1(ItemBase):

    objects = LayerManager()

    class Meta:
        proxy = True
        verbose_name = "Layer"
        verbose_name_plural = "Layers"

    @property
    def urls(self):
        urls = self._base_urls
        doc = self.get_document()
        urls.update({
            "resource": full_reverse("resource_detail", args=(self.pk, )),
            # remove detail and progress_page urls once InfoPanel has been fully
            # deprecated and volume summary has been updated.
            # note the geonode: prefix is still necessary until non-geonode
            # layer and document detail pages are created.
            "detail": f"/layers/geonode:{self.slug}" if self.slug else "",
            "progress_page": f"/layers/geonode:{self.pk}#georeference" if self.slug else "",
            # redundant, I know, but a patch for now
            "cog": settings.MEDIA_HOST.rstrip("/") + urls['image'],
        })
        if doc is not None:
            urls.update({
                "georeference": doc.urls['georeference'],
                "document": doc.urls['image'],
            })
        return urls

    def get_sessions(self, serialize=False):
        return self.get_document().get_sessions(serialize=serialize)

    def get_split_summary(self):
        return self.get_document().get_split_summary()

    def get_georeference_summary(self):
        return self.get_document().get_georeference_summary()

    def get_document(self):
        try:
            link = DocumentLink.objects.get(link_type="georeference", target_id=self.pk)
            document = link.source
        except DocumentLink.DoesNotExist:
            document = None
        return document

    def serialize(self, serialize_document=True, include_sessions=False):

        document = self.get_document()
        if document is not None:
            if serialize_document is True:
                document = document.serialize(serialize_layer=False)
            else:
                document = document.pk

        if include_sessions is True:
            session_data = self.get_sessions(serialize=True)
        else:
            session_data = None

        return {
            "id": self.pk,
            "title": self.title,
            "type": self.type,
            "slug": self.slug,
            "status": self.status,
            "urls": self.urls,
            "document": document,
            "extent": self.extent,
            "session_data": session_data,
        }

LINK_TYPE_CHOICES = (
    ("split","split"),
    ("georeference","georeference"),
)

class DocumentLink(models.Model):
    """Holds a linkage between a Document and another item. This model
    is essentially identical to DocumentResourceLink in GeoNode 3.2."""

    source = models.ForeignKey(
        Document,
        related_name='links',
        on_delete=models.CASCADE
    )
    target_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    target_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_type', 'target_id')
    link_type = models.CharField(
        choices = LINK_TYPE_CHOICES,
        max_length=25,
    )

    def __str__(self):
        return f"{self.source} --> {self.target}"


class LayerSetCategory(models.Model):

    class Meta:
        verbose_name_plural = "Set Categories"

    slug = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    display_name = models.CharField(max_length=50)
    is_geospatial = models.BooleanField(default=False)

    def __str__(self):
        return self.display_name if self.display_name else self.slug

class LayerSet(models.Model):

    volume = models.ForeignKey(
        "loc_insurancemaps.Volume",
        on_delete=models.CASCADE,
    )
    map = models.ForeignKey(
        "core.map",
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
    multimask = models.JSONField(
        null=True,
        blank=True
    )
    mosaic_geotiff = models.FileField(
        upload_to='mosaics',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    mosaic_json = models.FileField(
        upload_to='mosaics',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )

    def __str__(self):
        return f"{self.volume} - {self.category}"

    # TODO: deprecate this once the new layers are implemented
    def annotation_display_list(self):
        """For display in the admin interface only."""
        li = [f"<li><a href='/admin/georeference/itembase/{i.pk}/change'>{i.slug}</a></li>" for i in self.annotations]
        return mark_safe("<ul>"+"".join(li)+"</ul>")

    def layer_display_list(self):
        """For display in the admin interface only."""
        li = [f"<li><a href='/admin/core/layer/{i.pk}/change'>{i}</a></li>" for i in self.layers.all()]
        return mark_safe("<ul>"+"".join(li)+"</ul>")

    annotation_display_list.short_description = 'Annotations'
    layer_display_list.short_description = 'Layers'

    @property
    def is_geospatial(self):
        return True if self.category and self.category.is_geospatial else False

    @property
    def annotations(self):
        if self.is_geospatial:
            return LayerV1.objects.filter(vrs=self)
        else:
            return Document.objects.filter(vrs=self)

    @property
    def mosaic_cog_url(self):
        """ return the public url to the mosaic COG for this annotation set. If 
        no COG exists, return None."""
        url = None
        if self.mosaic_geotiff:
            url = settings.MEDIA_HOST.rstrip("/") + self.mosaic_geotiff.url
        return url

    @property
    def mosaic_json_url(self):
        """ return the public url to the mosaic JSON for this annotation set. If 
        no mosaic JSON exists, return None."""
        url = None
        if self.mosaic_json:
            url = settings.MEDIA_HOST.rstrip("/") + self.mosaic_json.url
        return url

    @property
    def extent(self):
        """Calculate an extent based on all layers in this annotation set. If
        this is not a spatial annotation set, or there are no layers, return None."""
        extent = None
        if self.is_geospatial:
            layer_extent_polygons = []
            for v in self.annotations:
                extent_poly = Polygon.from_bbox(v.extent)
                layer_extent_polygons.append(extent_poly)
            if len(layer_extent_polygons) > 0:
                extent = MultiPolygon(layer_extent_polygons, srid=4326).extent
        return extent

    @property
    def multimask_extent(self):
        """Calculate an extent based on all layers in this annotation set's
        multimask. If this is not a spatial annotation set, or there is no
        multimask, return None."""
        extent = None
        if self.is_geospatial and self.multimask:
            feature_polygons = []
            for v in self.multimask.values():
                poly = Polygon(v['geometry']['coordinates'][0])
                feature_polygons.append(poly)
            if len(feature_polygons) > 0:
                extent = MultiPolygon(feature_polygons, srid=4326).extent
        return extent

    @property
    def multimask_geojson(self):
        if self.multimask:
            multimask_geojson = {"type": "FeatureCollection", "features": []}
            for layer, geojson in self.multimask.items():
                geojson["properties"] = {"layer": layer}
                multimask_geojson['features'].append(geojson)
            return multimask_geojson
        else:
            return None
        
    def validate_multimask_geojson(self, multimask_geojson):
        errors = []
        for feature in multimask_geojson['features']:
            lyr = feature['properties']['layer']
            try:
                geom_str = json.dumps(feature['geometry'])
                g = GEOSGeometry(geom_str)
                if not g.valid:
                    logger.error(f"{self} | invalid mask: {lyr} - {g.valid_reason}")
                    errors.append((lyr, g.valid_reason))
            except Exception as e:
                logger.error(f"{self} | improper GeoJSON in multimask")
                errors.append((lyr, e))
        return errors
    
    def update_multimask_from_geojson(self, multimask_geojson):
        errors = self.validate_multimask_geojson(multimask_geojson)
        if errors:
            return errors
        
        if multimask_geojson['features']:
            self.multimask = {}
            for feature in multimask_geojson['features']:
                self.multimask[feature['properties']['layer']] = feature
        else:
            self.multimask = None
        self.save(update_fields=['multimask'])

    def generate_mosaic_vrt(self):
        """ A helpful reference from the BPLv used during the creation of this method:
        https://github.com/bplmaps/atlascope-utilities/blob/master/new-workflow/atlas-tools.py
        """

        gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
        gdal.SetConfigOption("GDAL_TIFF_INTERNAL_MASK", "YES")

        multimask_geojson = self.multimask_geojson
        multimask_file_name = f"multimask-{self.category.slug}-{self.volume.identifier}"
        multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
        with open(multimask_file, "w") as out:
            json.dump(multimask_geojson, out, indent=1)

        trim_list = []
        layer_extent_polygons = []
        for feature in multimask_geojson['features']:

            layer_name = feature['properties']['layer']

            layer = LayerV1.objects.get(slug=layer_name)
            if not layer.file:
                raise Exception(f"no layer file for this layer {layer_name}")

            if layer.extent:
                extent_poly = Polygon.from_bbox(layer.extent)
                layer_extent_polygons.append(extent_poly)

            latest_sesh = list(layer.get_document().georeference_sessions)[-1]
            in_path = latest_sesh.run(return_vrt=True)
            trim_name = os.path.basename(in_path).replace(".vrt", "_trim.vrt")
            out_path = os.path.join(settings.TEMP_DIR, trim_name)

            wo = gdal.WarpOptions(
                format="VRT",
                dstSRS = "EPSG:3857",
                cutlineDSName = multimask_file,
                cutlineLayer = multimask_file_name,
                cutlineWhere = f"layer='{layer_name}'",
                cropToCutline = True,
                # srcAlpha = True,
                # dstAlpha = True,
                # creationOptions= [
                #     'COMPRESS=JPEG',
                # ]
                # creationOptions= [
                #     'COMPRESS=DEFLATE',
                #     'PREDICTOR=2',
                # ]
            )
            gdal.Warp(out_path, in_path, options=wo)
            print("warped")

            trim_list.append(out_path)

        if len(layer_extent_polygons) > 0:
            multi = MultiPolygon(layer_extent_polygons, srid=4326)

        bounds = multi.transform(3857, True).extent
        vo = gdal.BuildVRTOptions(
            resolution = 'highest',
            outputSRS="EPSG:3857",
            outputBounds=bounds,
            separate = False,
        )
        print("building vrt")

        mosaic_vrt = os.path.join(settings.TEMP_DIR, f"{self.volume.identifier}-{self.category.slug}.vrt")
        gdal.BuildVRT(mosaic_vrt, trim_list, options=vo)

        return mosaic_vrt

    def generate_mosaic_cog(self):

        start = datetime.now()

        mosaic_vrt = self.generate_mosaic_vrt()

        print("building final geotiff")

        to = gdal.TranslateOptions(
            format="COG",
            creationOptions = [
                "BIGTIFF=YES",
                "COMPRESS=JPEG",
                "TILING_SCHEME=GoogleMapsCompatible",
            ],
        )

        mosaic_tif = mosaic_vrt.replace(".vrt", ".tif")
        gdal.Translate(mosaic_tif, mosaic_vrt, options=to)

        existing_file_path = None
        if self.mosaic_geotiff:
            existing_file_path = self.mosaic_geotiff.path

        file_name = f"{self.volume.identifier}-{self.category.slug}__{datetime.now().strftime('%Y-%m-%d')}__{random_alnum(6)}.tif"

        with open(mosaic_tif, 'rb') as f:
            self.mosaic_geotiff.save(file_name, File(f))

        os.remove(mosaic_tif)
        if existing_file_path:
            os.remove(existing_file_path)

        print(f"completed - elapsed time: {datetime.now() - start}")

    def generate_mosaic_json(self, trim_all=False):

        def write_trim_feature_cache(feature, file_path):
            with open(file_path, "w") as f:
                json.dump(feature, f, indent=2)

        def read_trim_feature_cache(file_path):
            with open(file_path, "r") as f:
                feature = json.load(f)
            return feature

        logger.info(f"{self.vol.identifier} | generating mosaic json")

        multimask_geojson = self.vol.multimask_geojson
        multimask_file_name = f"multimask-{self.vol.identifier}"
        multimask_file = os.path.join(settings.TEMP_DIR, f"{multimask_file_name}.geojson")
        with open(multimask_file, "w") as out:
            json.dump(multimask_geojson, out, indent=1)

        logger.debug(f"{self.vol.identifier} | multimask loaded")
        logger.info(f"{self.vol.identifier} | iterating and trimming layers")
        trim_list = []
        for feature in multimask_geojson['features']:

            layer_name = feature['properties']['layer']
            layer = LayerV1.objects.get(slug=layer_name)
            if not layer.file:
                logger.error(f"{self.vol.identifier} | no layer file for this layer {layer_name}")
                raise Exception(f"no layer file for this layer {layer_name}")
            in_path = layer.file.path

            layer_dir = os.path.dirname(in_path)
            file_name = os.path.basename(in_path)
            logger.debug(f"{self.vol.identifier} | processing layer file {file_name}")

            file_root = os.path.splitext(file_name)[0]
            existing_trimmed_tif = glob.glob(f"{layer_dir}/{file_root}*_trim.tif")
            print(existing_trimmed_tif)

            feat_cache_path = in_path.replace(".tif", "_trim-feature.json")
            if os.path.isfile(feat_cache_path):
                cached_feature = read_trim_feature_cache(feat_cache_path)
                logger.debug(f"{self.vol.identifier} | using cached trim json boundary")
            else:
                cached_feature = None
                write_trim_feature_cache(feature, feat_cache_path)

            unique_id = random_alnum(6)
            trim_vrt_path = in_path.replace(".tif", f"_{unique_id}_trim.vrt")
            out_path = trim_vrt_path.replace(".vrt", ".tif")

            # compare this multimask feature to the cached one for this layer
            # and only (re)create a trimmed tif if they do not match
            if feature != cached_feature or trim_all is True:

                wo = gdal.WarpOptions(
                    format="VRT",
                    dstSRS = "EPSG:3857",
                    cutlineDSName = multimask_file,
                    cutlineLayer = multimask_file_name,
                    cutlineWhere = f"layer='{layer_name}'",
                    cropToCutline = True,
                    creationOptions = ['COMPRESS=LZW', 'BIGTIFF=YES'],
                    resampleAlg = 'cubic',
                    dstAlpha = False,
                    dstNodata = "255 255 255",
                )
                gdal.Warp(trim_vrt_path, in_path, options=wo)

                to = gdal.TranslateOptions(
                    format="GTiff",
                    bandList = [1,2,3],
                    creationOptions = [
                        "TILED=YES",
                        "COMPRESS=LZW",
                        "PREDICTOR=2",
                        "NUM_THREADS=ALL_CPUS",
                        ## the following is apparently in the COG spec but doesn't work??
                        # "COPY_SOURCE_OVERVIEWS=YES",
                    ],
                )

                logger.debug(f"writing trimmed tif {os.path.basename(out_path)}")
                gdal.Translate(out_path, trim_vrt_path, options=to)
                write_trim_feature_cache(feature, feat_cache_path)

                img = gdal.Open(out_path, 1)
                if img is None:
                    logger.warn(f"{self.vol.identifier} | file was not properly created, omitting: {file_name}")
                    continue   
                logger.debug(f"{self.vol.identifier} | building overview: {file_name}")
                gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
                gdal.SetConfigOption("PREDICTOR", "2")
                gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
                img.BuildOverviews("AVERAGE", [2, 4, 8, 16])

            else:
                logger.debug(f"{self.vol.identifier} | using existing trimmed tif {file_name}")

            trim_list.append(out_path)

        trim_urls = [
            i.replace(os.path.dirname(settings.MEDIA_ROOT), settings.MEDIA_HOST.rstrip("/")) \
                for i in trim_list
        ]
        logger.info(f"{self.vol.identifier} | writing mosaic from {len(trim_urls)} trimmed tifs")
        mosaic_data = MosaicJSON.from_urls(trim_urls, minzoom=14)
        mosaic_json_path = os.path.join(settings.TEMP_DIR, f"{self.vol.identifier}-mosaic.json")
        with MosaicBackend(mosaic_json_path, mosaic_def=mosaic_data) as mosaic:
            mosaic.write(overwrite=True)

        with open(mosaic_json_path, 'rb') as f:
            self.vol.mosaic_json = File(f, name=os.path.basename(mosaic_json_path))
            self.vol.save()

        logger.info(f"{self.vol.identifier} | mosaic created: {os.path.basename(mosaic_json_path)}")
        return mosaic_json_path
