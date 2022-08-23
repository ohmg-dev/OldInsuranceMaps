import uuid
import json
import logging
from osgeo import gdal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.functional import cached_property

from geonode.documents.models import Document, DocumentResourceLink
from geonode.layers.models import Layer
from geonode.geoserver.helpers import save_style

from geonode.base.bbox_utils import BBOXHelper, polygon_from_bbox
from geonode.base.models import Region
from geonode.notifications_helper import (
    get_notification_recipients,
    send_notification,
)

from georeference.utils import (
    get_gs_catalog,
)

logger = logging.getLogger(__name__)

class SplitDocumentLink(DocumentResourceLink):
    """
    Inherits from the DocumentResourceLink in GeoNode. This allows
    new instances of this model to be used by GeoNode in a default
    manner, while this app can use them in its own way.
    
    Used to create a link between split documents and their children.
    """

    class Meta:
        verbose_name = "Split Document Link"
        verbose_name_plural = "Split Document Links"

    def __str__(self):
        child = Document.objects.get(pk=self.object_id)
        return f"{self.document.__str__()} --> {child.__str__()}"


class GeoreferencedDocumentLink(DocumentResourceLink):
    """
    Inherits from the DocumentResourceLink in GeoNode. This allows
    new instances of this model to be used by GeoNode in a default
    manner, while this app can use them in its own way.

    Used to create a link between georeferenced documents and the
    resulting layer.
    """

    class Meta:
        verbose_name = "Georeferenced Document Link"
        verbose_name_plural = "Georeferenced Document Links"

    def __str__(self):
        try:
            layer_name = Layer.objects.get(pk=self.object_id).alternate
        except Layer.DoesNotExist:
            layer_name = "None"
        return f"{self.document.__str__()} --> {layer_name}"


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

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    crs_epsg = models.IntegerField(null=True, blank=True)
    transformation = models.CharField(
        null=True,
        blank=True,
        choices=TRANSFORMATION_CHOICES,
        max_length=20,
    )

    def __str__(self):
        return self.document.title

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
            lat = coords[0]
            lng = coords[1]
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
                    "coordinates": [lng, lat]
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

        group, group_created = GCPGroup.objects.get_or_create(document=document)

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


class LayerMask(models.Model):

    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    polygon = models.PolygonField(srid=3857)

    def as_sld(self, indent=False):

        sld = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
 xmlns="http://www.opengis.net/sld"
 xmlns:ogc="http://www.opengis.net/ogc"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<NamedLayer>
 <Name>{self.layer.workspace}:{self.layer.name}</Name>
 <UserStyle IsDefault="true">
  <FeatureTypeStyle>
   <Transformation>
    <ogc:Function name="gs:CropCoverage">
     <ogc:Function name="parameter">
      <ogc:Literal>coverage</ogc:Literal>
     </ogc:Function>
     <ogc:Function name="parameter">
      <ogc:Literal>cropShape</ogc:Literal>
      <ogc:Literal>{self.polygon.wkt}</ogc:Literal>
     </ogc:Function>
    </ogc:Function>
   </Transformation>
   <Rule>
    <RasterSymbolizer>
      <Opacity>1</Opacity>
    </RasterSymbolizer>
   </Rule>
  </FeatureTypeStyle>
 </UserStyle>
</NamedLayer>
</StyledLayerDescriptor>'''

        if indent is False:
            sld = " ".join([i.strip() for i in sld.splitlines()])
            sld = sld.replace("> <","><")

        return sld

    def apply_mask(self):

        cat = get_gs_catalog()

        gs_full_style = cat.get_style(self.layer.name, workspace="geonode")
        trim_style_name = f"{self.layer.name}_trim"

        # create (overwrite if existing) trim style in GeoServer using mask sld
        gs_trim_style = cat.create_style(
            trim_style_name,
            self.as_sld(),
            overwrite=True,
            workspace="geonode",
        )

        # get the GeoServer layer for this GeoNode layer
        gs_layer = cat.get_layer(self.layer.name)

        # add the full and trim styles to the GeoServer alternate style list
        gs_alt_styles = gs_layer._get_alternate_styles()
        gs_alt_styles += [gs_full_style, gs_trim_style]
        gs_layer._set_alternate_styles(gs_alt_styles)

        # set the trim style as the default in GeoServer
        gs_layer._set_default_style(gs_trim_style)

        # save these changes to the GeoServer layer
        cat.save(gs_layer)

        # create/update the GeoNode Style object for the trim style
        trim_style_gn = save_style(gs_trim_style, self.layer)

        # add new trim style to GeoNode list styles, set as default, save
        self.layer.styles.add(trim_style_gn)
        self.layer.default_style = trim_style_gn
        self.layer.save()

        # update thumbnail with new trim style
#        thumb = create_thumbnail(self.layer, overwrite=True)
#        self.layer.thumbnail_url = thumb
#        self.layer.save()


# set ResourceBase, Document, and Layer to inherit object for now,
# i.e. don't register as models yet. Still much work to do.
class ResourceBase(object):

    GEOREF_STATUS_CHOICES = (
        ("unprepared", "Unprepared"),
        ("needs review", "Needs Review"),
        ("Splitting - in progress"),
        ("split", "Split"),
        ("prepared", "Prepared"),
        ("georeferencing", "Georeferencing - in progress"),
        ("georeferenced", "Georeferenced"),
        ("trimming", "Trimming - in progress"),
        ("trimmed", "Trimmed"),
    )

    abstract_help_text = _(
        'brief narrative summary of the content of the resource(s)')
    date_help_text = _('reference date for the cited resource')
    date_type_help_text = _('identification of when a given event occurred')
    edition_help_text = _('version of the cited resource')
    attribution_help_text = _(
        'authority or function assigned, as to a ruler, legislative assembly, delegate, or the like.')
    doi_help_text = _(
        'a DOI will be added by Admin before publication.')
    purpose_help_text = _(
        'summary of the intentions with which the resource(s) was developed')
    maintenance_frequency_help_text = _(
        'frequency with which modifications and deletions are made to the data after '
        'it is first produced')
    keywords_help_text = _(
        'commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject '
        '(space or comma-separated)')
    tkeywords_help_text = _(
        'formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject '
        '(space or comma-separated)')
    regions_help_text = _('keyword identifies a location')
    restriction_code_type_help_text = _(
        'limitation(s) placed upon the access or use of the data.')
    constraints_other_help_text = _(
        'other restrictions and legal prerequisites for accessing and using the resource or'
        ' metadata')
    license_help_text = _('license of the dataset')
    language_help_text = _('language used within the dataset')
    category_help_text = _(
        'high-level geographic data thematic classification to assist in the grouping and search of '
        'available geographic data sets.')
    spatial_representation_type_help_text = _(
        'method used to represent geographic information in the dataset.')
    temporal_extent_start_help_text = _(
        'time period covered by the content of the dataset (start)')
    temporal_extent_end_help_text = _(
        'time period covered by the content of the dataset (end)')
    data_quality_statement_help_text = _(
        'general explanation of the data producer\'s knowledge about the lineage of a'
        ' dataset')
    # internal fields
    uuid = models.CharField(max_length=36)
    title = models.CharField(_('title'), max_length=255, help_text=_(
        'name by which the cited resource is known'))
    abstract = models.TextField(
        _('abstract'),
        max_length=2000,
        blank=True,
        help_text=abstract_help_text)
    purpose = models.TextField(
        _('purpose'),
        max_length=500,
        null=True,
        blank=True,
        help_text=purpose_help_text)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='owned_resource',
        verbose_name=_("Owner"),
        on_delete=models.PROTECT)
    contacts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ContactRole')
    alternate = models.CharField(max_length=128, null=True, blank=True)
    date = models.DateTimeField(
        _('date'),
        default=timezone.now,
        help_text=date_help_text)
    edition = models.CharField(
        _('edition'),
        max_length=255,
        blank=True,
        null=True,
        help_text=edition_help_text)
    attribution = models.CharField(
        _('Attribution'),
        max_length=2048,
        blank=True,
        null=True,
        help_text=attribution_help_text)
    doi = models.CharField(
        _('DOI'),
        max_length=255,
        blank=True,
        null=True,
        help_text=doi_help_text)
    georef_status = models.CharField(
        verbose_name=_('georeferencing status'),
        blank=True,
        null=True,
        default=GEOREF_STATUS_CHOICES[0][0],
        choices=GEOREF_STATUS_CHOICES)
    regions = models.ManyToManyField(
        Region,
        verbose_name=_('keywords region'),
        null=True,
        blank=True,
        help_text=regions_help_text)

    data_quality_statement = models.TextField(
        _('data quality statement'),
        max_length=2000,
        blank=True,
        null=True,
        help_text=data_quality_statement_help_text)
    # group = models.ForeignKey(
    #     Group,
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL)

    bbox_polygon = models.PolygonField(null=True, blank=True)

    srid = models.CharField(
        max_length=30,
        blank=False,
        null=False,
        default='EPSG:4326')

    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    featured = models.BooleanField(_("Featured"), default=False, help_text=_(
        'Should this resource be advertised in home page?'))
    is_published = models.BooleanField(
        _("Is Published"),
        default=True,
        help_text=_('Should this resource be published and searchable?'))
    is_approved = models.BooleanField(
        _("Approved"),
        default=True,
        help_text=_('Is this resource validated from a publisher or editor?'))

    # fields necessary for the apis
    thumbnail_url = models.TextField(_("Thumbnail url"), null=True, blank=True)
    detail_url = models.CharField(max_length=255, null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    # fields controlling security state
    dirty_state = models.BooleanField(
        _("Dirty State"),
        default=False,
        help_text=_('Security Rules Are Not Synched with GeoServer!'))

    metadata_only = models.BooleanField(
        _("Metadata"),
        default=False,
        help_text=_('If true, will be excluded from search'))

    class Meta:
        # custom permissions,
        # add, change and delete are standard in django-guardian
        permissions = (
            # ('view_resourcebase', 'Can view resource'),
            ('change_resourcebase_permissions', 'Can change resource permissions'),
            ('download_resourcebase', 'Can download resource'),
            ('publish_resourcebase', 'Can publish resource'),
            ('change_resourcebase_metadata', 'Can change resource metadata'),
        )

    def __str__(self):
        return str(self.title)

    @property
    def raw_abstract(self):
        return self._remove_html_tags(self.abstract)

    @property
    def raw_purpose(self):
        return self._remove_html_tags(self.purpose)

    @property
    def raw_constraints_other(self):
        return self._remove_html_tags(self.constraints_other)

    @property
    def raw_supplemental_information(self):
        return self._remove_html_tags(self.supplemental_information)

    @property
    def raw_data_quality_statement(self):
        return self._remove_html_tags(self.data_quality_statement)

    def save(self, notify=False, *args, **kwargs):
        """
        Send a notification when a resource is created or updated
        """

        if hasattr(self, 'class_name') and (self.pk is None or notify):
            if self.pk is None and self.title:
                # Resource Created

                notice_type_label = f'{self.class_name.lower()}_created'
                recipients = get_notification_recipients(notice_type_label, resource=self)
                send_notification(recipients, notice_type_label, {'resource': self})
            elif self.pk:
                # Resource Updated
                _notification_sent = False

                # Approval Notifications Here
                if not _notification_sent and settings.ADMIN_MODERATE_UPLOADS and \
                   not self.__is_approved and self.is_approved:
                    # Set "approved" workflow permissions
                    self.set_workflow_perms(approved=True)

                    # Send "approved" notification
                    notice_type_label = f'{self.class_name.lower()}_approved'
                    recipients = get_notification_recipients(notice_type_label, resource=self)
                    send_notification(recipients, notice_type_label, {'resource': self})
                    _notification_sent = True

                # Publishing Notifications Here
                if not _notification_sent and settings.RESOURCE_PUBLISHING and \
                   not self.__is_published and self.is_published:
                    # Set "published" workflow permissions
                    self.set_workflow_perms(published=True)

                    # Send "published" notification
                    notice_type_label = f'{self.class_name.lower()}_published'
                    recipients = get_notification_recipients(notice_type_label, resource=self)
                    send_notification(recipients, notice_type_label, {'resource': self})
                    _notification_sent = True

                # Updated Notifications Here
                if not _notification_sent:
                    notice_type_label = f'{self.class_name.lower()}_updated'
                    recipients = get_notification_recipients(notice_type_label, resource=self)
                    send_notification(recipients, notice_type_label, {'resource': self})

        super(ResourceBase, self).save(*args, **kwargs)
        self.__is_approved = self.is_approved
        self.__is_published = self.is_published

    def delete(self, notify=True, *args, **kwargs):
        """
        Send a notification when a layer, map or document is deleted
        """
        if hasattr(self, 'class_name') and notify:
            notice_type_label = f'{self.class_name.lower()}_deleted'
            recipients = get_notification_recipients(notice_type_label, resource=self)
            send_notification(recipients, notice_type_label, {'resource': self})

        super(ResourceBase, self).delete(*args, **kwargs)

    def get_upload_session(self):
        raise NotImplementedError()

    @property
    def site_url(self):
        return settings.SITEURL

    @property
    def creator(self):
        return self.owner.get_full_name() or self.owner.username

    @property
    def perms(self):
        return []

    @property
    def organizationname(self):
        return self.owner.organization

    @property
    def restriction_code(self):
        return self.restriction_code_type.gn_description

    @property
    def publisher(self):
        return self.poc.get_full_name() or self.poc.username

    @property
    def contributor(self):
        return self.metadata_author.get_full_name() or self.metadata_author.username

    @property
    def topiccategory(self):
        return self.category.identifier

    @property
    def csw_crs(self):
        return 'EPSG:4326'

    @property
    def group_name(self):
        if self.group:
            return str(self.group).encode("utf-8", "replace")
        return None



    def keyword_list(self):
        return [kw.name for kw in self.keywords.all()]

    def keyword_slug_list(self):
        return [kw.slug for kw in self.keywords.all()]

    def region_name_list(self):
        return [region.name for region in self.regions.all()]

    def set_dirty_state(self):
        self.dirty_state = True
        ResourceBase.objects.filter(id=self.id).update(dirty_state=True)

    def clear_dirty_state(self):
        self.dirty_state = False
        ResourceBase.objects.filter(id=self.id).update(dirty_state=False)

    @property
    def processed(self):
        return not self.dirty_state

    @property
    def keyword_csv(self):
        try:
            keywords_qs = self.get_real_instance().keywords.all()
            if keywords_qs:
                return ','.join(kw.name for kw in keywords_qs)
            else:
                return ''
        except Exception:
            return ''


class Document(object):
    pass

class Layer(object):

    # @property
    # def bbox(self):
    #     """BBOX is in the format: [x0, x1, y0, y1, srid]."""
    #     if self.bbox_polygon:
    #         match = re.match(r'^(EPSG:)?(?P<srid>\d{4,6})$', self.srid)
    #         srid = int(match.group('srid')) if match else 4326
    #         bbox = BBOXHelper(self.bbox_polygon.extent)
    #         return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, f"EPSG:{srid}"]
    #     bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
    #     return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]


    # @property
    # def bbox_string(self):
    #     """BBOX is in the format: [x0, y0, x1, y1]. Provides backwards compatibility
    #     after transition to polygons."""
    #     if self.bbox_polygon:
    #         bbox = BBOXHelper.from_xy(self.bbox[:4])

    #         return f"{bbox.xmin:.7f},{bbox.ymin:.7f},{bbox.xmax:.7f},{bbox.ymax:.7f}"
    #     bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
    #     return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    # @property
    # def bbox_helper(self):
    #     if self.bbox_polygon:
    #         return BBOXHelper(self.bbox_polygon.extent)
    #     bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
    #     return [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax, "EPSG:4326"]

    # @cached_property
    # def bbox_x0(self):
    #     if self.bbox_polygon:
    #         return self.bbox[0]
    #     return None

    # @cached_property
    # def bbox_x1(self):
    #     if self.bbox_polygon:
    #         return self.bbox[1]
    #     return None

    # @cached_property
    # def bbox_y0(self):
    #     if self.bbox_polygon:
    #         return self.bbox[2]
    #     return None

    # @cached_property
    # def bbox_y1(self):
    #     if self.bbox_polygon:
    #         return self.bbox[3]
    #     return None

    # @property
    # def geographic_bounding_box(self):
    #     """
    #     Returns an EWKT representation of the bounding box in EPSG:4326
    #     """
    #     if self.ll_bbox_polygon:
    #         bbox = polygon_from_bbox(self.ll_bbox_polygon.extent, 4326)
    #         return str(bbox)
    #     else:
    #         bbox = BBOXHelper.from_xy([-180, 180, -90, 90])
    #         return bbox_to_wkt(
    #             bbox.xmin,
    #             bbox.xmax,
    #             bbox.ymin,
    #             bbox.ymax,
    #             srid='EPSG:4326')

    # def set_bbox_polygon(self, bbox, srid):
    #     """
    #     Set `bbox_polygon` from bbox values.

    #     :param bbox: list or tuple formatted as
    #         [xmin, ymin, xmax, ymax]
    #     :param srid: srid as string (e.g. 'EPSG:4326' or '4326')
    #     """
    #     bbox_polygon = Polygon.from_bbox(bbox)
    #     self.bbox_polygon = bbox_polygon.clone()
    #     self.srid = srid
    #     if srid == 4326 or srid == "EPSG:4326":
    #         self.ll_bbox_polygon = bbox_polygon
    #     else:
    #         match = re.match(r'^(EPSG:)?(?P<srid>\d{4,6})$', str(srid))
    #         bbox_polygon.srid = int(match.group('srid')) if match else 4326
    #         try:
    #             self.ll_bbox_polygon = bbox_polygon.transform(4326, clone=True)
    #         except Exception as e:
    #             logger.error(e)
    #             self.ll_bbox_polygon = bbox_polygon

    # def set_bounds_from_center_and_zoom(self, center_x, center_y, zoom):
    #     """
    #     Calculate zoom level and center coordinates in mercator.
    #     """
    #     self.center_x = center_x
    #     self.center_y = center_y
    #     self.zoom = zoom

    #     deg_len_equator = 40075160.0 / 360.0

    #     # covert center in lat lon
    #     def get_lon_lat():
    #         wgs84 = Proj(init='epsg:4326')
    #         mercator = Proj(init='epsg:3857')
    #         lon, lat = transform(mercator, wgs84, center_x, center_y)
    #         return lon, lat

    #     # calculate the degree length at this latitude
    #     def deg_len():
    #         lon, lat = get_lon_lat()
    #         return math.cos(lat) * deg_len_equator

    #     lon, lat = get_lon_lat()

    #     # taken from http://wiki.openstreetmap.org/wiki/Zoom_levels
    #     # it might be not precise but enough for the purpose
    #     distance_per_pixel = 40075160 * math.cos(lat) / 2 ** (zoom + 8)

    #     # calculate the distance from the center of the map in degrees
    #     # we use the calculated degree length on the x axis and the
    #     # normal degree length on the y axis assumin that it does not change

    #     # Assuming a map of 1000 px of width and 700 px of height
    #     distance_x_degrees = distance_per_pixel * 500.0 / deg_len()
    #     distance_y_degrees = distance_per_pixel * 350.0 / deg_len_equator

    #     bbox_x0 = lon - distance_x_degrees
    #     bbox_x1 = lon + distance_x_degrees
    #     bbox_y0 = lat - distance_y_degrees
    #     bbox_y1 = lat + distance_y_degrees
    #     self.srid = 'EPSG:4326'
    #     self.set_bbox_polygon((bbox_x0, bbox_y0, bbox_x1, bbox_y1), self.srid)

    # def set_bounds_from_bbox(self, bbox, srid):
    #     """
    #     Calculate zoom level and center coordinates in mercator.

    #     :param bbox: BBOX is either a `geos.Pologyon` or in the
    #         format: [x0, x1, y0, y1], which is:
    #         [min lon, max lon, min lat, max lat] or
    #         [xmin, xmax, ymin, ymax]
    #     :type bbox: list
    #     """
    #     if isinstance(bbox, Polygon):
    #         self.set_bbox_polygon(bbox.extent, srid)
    #         self.set_center_zoom()
    #         return
    #     elif isinstance(bbox, list):
    #         self.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], srid)
    #         self.set_center_zoom()
    #         return

    #     if not bbox or len(bbox) < 4:
    #         raise ValidationError(
    #             f'Bounding Box cannot be empty {self.name} for a given resource')
    #     if not srid:
    #         raise ValidationError(
    #             f'Projection cannot be empty {self.name} for a given resource')

    #     self.srid = srid
    #     self.set_bbox_polygon(
    #         (bbox[0], bbox[2], bbox[1], bbox[3]), srid)
    #     self.set_center_zoom()


    # def get_tiles_url(self):
    #     """Return URL for Z/Y/X mapping clients or None if it does not exist.
    #     """
    #     try:
    #         tiles_link = self.link_set.get(name='Tiles')
    #     except Link.DoesNotExist:
    #         return None
    #     else:
    #         return tiles_link.url

    pass
