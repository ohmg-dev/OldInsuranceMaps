import uuid
import json
import logging
from osgeo import gdal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.db import models

from geonode.documents.models import Document, DocumentResourceLink
from geonode.layers.models import Layer
from geonode.geoserver.helpers import save_style

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
