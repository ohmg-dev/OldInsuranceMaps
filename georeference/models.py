import os
import uuid
import json
from osgeo import gdal, osr
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.files import File
from django.db.models import signals
from django.dispatch import receiver
from django.utils import timezone

from geonode.documents.models import Document, DocumentResourceLink
from geonode.layers.models import Layer, Style
from geonode.layers.utils import file_upload
from geonode.thumbs.thumbnails import create_thumbnail
from geonode.geoserver.helpers import save_style

from .georeferencer import Georeferencer
from .splitter import Splitter
from .utils import (
    get_gs_catalog,
    full_reverse,
    TKeywordManager,
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

class SplitEvaluation(models.Model):

    class Meta:
        verbose_name = "Split Evaluation"
        verbose_name_plural = "Split Evaluations"

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    split_needed = models.BooleanField(default=None, null=True, blank=True)
    cutlines = JSONField(default=None, null=True, blank=True)
    divisions = JSONField(default=None, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        blank=False)

    def __str__(self):
        return f"{self.document.__str__()} - {self.user} - {self.created}"

    @property
    def georeferenced_downstream(self):
        """Returns True if the related document or its children (if it
        has been split) have already been georeferenced."""

        if self.split_needed is True:
            docs_to_check = self.get_children()
        else:
            docs_to_check = [self.document]

        tkm = TKeywordManager()
        return any([tkm.is_georeferenced(d) for d in docs_to_check])

    def get_children(self):
        """Returns a list of all the child documents created by this
        determination."""

        ct = ContentType.objects.get(app_label="documents", model="document")
        child_ids = SplitDocumentLink.objects.filter(
            document=self.document,
            content_type=ct,
        ).values_list("object_id", flat=True)
        return list(Document.objects.filter(pk__in=child_ids))

    def preview_divisions(self):

        if self.cutlines is None:
            return []

        s = Splitter(image_file=self.document.doc_file.path)
        return s.generate_divisions(self.cutlines)

    def run(self):
        """
        Runs the document split process based on prestored segmentation info
        that has been generated for this document. New Documents are made for
        each child image, SplitDocumentLinks are created to link this parent
        Document with its children. The parent document is also marked as
        metadata_only so that it no longer shows up in the search page lists.
        """

        tkm = TKeywordManager()
        tkm.set_status(self.document, "splitting")

        if self.split_needed is False:
            tkm.set_status(self.document, "prepared")
            self.document.metadata_only = False
            self.document.save()
        else:
            s = Splitter(image_file=self.document.doc_file.path)
            s.generate_divisions(self.cutlines)
            new_images = s.split_image()

            for n, file_path in enumerate(new_images, start=1):

                fname = os.path.basename(file_path)
                new_doc = Document.objects.get(pk=self.document.pk)
                new_doc.pk = None
                new_doc.id = None
                new_doc.uuid = None
                new_doc.thumbnail_url = None
                new_doc.metadata_only = False
                new_doc.title = f"{self.document.title} [{n}]"
                with open(file_path, "rb") as openf:
                    new_doc.doc_file.save(fname, File(openf))
                new_doc.save()

                os.remove(file_path)

                ct = ContentType.objects.get(app_label="documents", model="document")
                SplitDocumentLink.objects.create(
                    document=self.document,
                    content_type=ct,
                    object_id=new_doc.pk,
                )

                for r in self.document.regions.all():
                    new_doc.regions.add(r)
                tkm.set_status(new_doc, "prepared")

            if len(new_images) > 1:
                self.document.metadata_only = True
                self.document.save()

            tkm.set_status(self.document, "split")

        return

    def cleanup(self):
        """Method called with pre_delete signal that cleans up resulting
        documents from previous split operations, if necessary. This is
        meant to provide a "reset" capability for SplitDeterminations."""

        # first check to make sure this determination can be reversed.
        if self.georeferenced_downstream is True:
            logger.warn(f"Removing SplitEvaluation {self.pk} even though downstream georeferencing has occurred.")

        # if a split was made, remove all descendant documents before deleting
        if self.split_needed is True:
            for child in self.get_children():
                child.delete()

        SplitDocumentLink.objects.filter(document=self.document).delete()

        TKeywordManager().set_status(self.document, "unprepared")
        self.document.metadata_only = False
        self.document.save()

    def serialize(self):
        return {
            "allow_reset": not self.georeferenced_downstream,
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
            },
            "date": (self.created.month, self.created.day, self.created.year),
            "date_str": self.created.strftime("%Y-%m-%d"),
            "datetime": self.created.strftime("%Y-%m-%d - %H:%M"),
            "split_needed": self.split_needed,
            "divisions_ct": len(self.get_children()),
        }



class GeoreferenceSession(models.Model):

    class Meta:
        verbose_name = "Georeference Session"
        verbose_name_plural = "Georeference Sessions"

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    layer = models.ForeignKey(Layer, models.SET_NULL, null=True, blank=True)
    gcps_used = JSONField(null=True, blank=True)
    transformation_used = models.CharField(null=True, blank=True, max_length=20)
    crs_epsg_used = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        null=False,
        blank=False)
    status = models.CharField(
        default="initializing",
        max_length=100,
    )
    note = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )

    def __str__(self):
        return f"{self.document.title} - {self.created}"

    def run(self):

        tkm = TKeywordManager()
        tkm.set_status(self.document, "georeferencing")
        self.update_status("initializing georeferencer")
        try:
            g = Georeferencer(
                transformation=self.transformation_used,
                epsg_code=self.crs_epsg_used,
            )
            g.load_gcps_from_geojson(self.gcps_used)
        except Exception as e:
            self.update_status("failed")
            self.note = f"{e.message}"
            self.save()
            # revert to previous tkeyword status
            tkm.set_status(self.document, "prepared")
            return None
        self.update_status("georeferencing")
        try:
            out_path = g.make_tif(self.document.doc_file.path)
        except Exception as e:
            self.update_status("failed")
            self.note = f"{e.message}"
            self.save()
            # revert to previous tkeyword status
            tkm.set_status(self.document, "prepared")
            return None

        # self.transformation_used = g.transformation["id"]
        self.update_status("creating layer")

        ## need to remove commas from the titles, otherwise the layer will not
        ## be valid in the catalog list when trying to add it to a Map. the 
        ## message in the catalog will read "Missing OGC reference metadata".
        title = self.document.title.replace(",", " -")

        ## first look to see if there is a layer alreaded linked to this document.
        ## this would indicate that it has already been georeferenced, and in this
        ## case the existing layer should be overwritten.
        existing_layer = None
        try:
            link = GeoreferencedDocumentLink.objects.get(document=self.document)
            existing_layer = Layer.objects.get(pk=link.object_id)
        except (GeoreferencedDocumentLink.DoesNotExist, Layer.DoesNotExist):
            pass

        ## create the layer, passing in the existing_layer if present
        layer = file_upload(
            out_path,
            layer=existing_layer,
            overwrite=True,
            title=title,
            user=self.user,
        )

        ## if there was no existing layer, create a new link between the
        ## document and the new layer
        if existing_layer is None:
            ct = ContentType.objects.get(app_label="layers", model="layer")
            GeoreferencedDocumentLink.objects.create(
                document=self.document,
                content_type=ct,
                object_id=layer.pk,
            )

            # set attributes in the layer straight from the document
            for keyword in self.document.keywords.all():
                layer.keywords.add(keyword)
            for region in self.document.regions.all():
                layer.regions.add(region)
            Layer.objects.filter(pk=layer.pk).update(
                date=self.document.date,
                abstract=self.document.abstract,
                category=self.document.category,
                license=self.document.license,
                restriction_code_type=self.document.restriction_code_type,
                attribution=self.document.attribution,
            )

        ## if there was an existing layer that's been overwritten, regenerate thumb.
        else:
            self.update_status("regenerating thumbnail")
            thumb = create_thumbnail(layer, overwrite=True)
            Layer.objects.filter(pk=layer.pk).update(thumbnail_url=thumb)

        self.layer = layer
        self.update_status("saving control points")

        # save the successful gcps to the canonical GCPGroup for the document
        GCPGroup().save_from_geojson(
            self.gcps_used, 
            self.document, 
            self.transformation_used
        )

        tkm.set_status(self.document, "georeferenced")
        tkm.set_status(layer, "georeferenced")

        self.update_status("completed")
        self.save()

        return layer

    def update_status(self, status):
        logger.debug(f"GeoreferenceSession {self.id} | set status: {status}")
        self.status = status
        self.save(update_fields=['status'])

    def serialize(self):
        return {
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
            },
            "date": (self.created.month, self.created.day, self.created.year),
            "date_str": self.created.strftime("%Y-%m-%d"),
            "datetime": self.created.strftime("%Y-%m-%d - %H:%M"),
            "gcps_geojson": self.gcps_used,
            "gcps_ct": len(self.gcps_used["features"]),
            "transformation": self.transformation_used,
            "epsg": self.crs_epsg_used,
            "status": self.status,
        }


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

    def save_from_geojson(self, geojson, document, transformation=None):
        print("saving gcps")

        group, created = GCPGroup.objects.get_or_create(document=document)

        group.crs_epsg = 3857 # don't see this changing any time soon...
        group.transformation = transformation
        group.save()

        # first remove any existing gcps that have been deleted
        for gcp in group.gcps:
            if str(gcp.id) not in [i['properties'].get('id') for i in geojson['features']]:
                print(f"deleting gcp {gcp.id}")
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
            print("new gcp created?", created)

            pixel_x = feature['properties']['image'][0]
            pixel_y = feature['properties']['image'][1]
            new_pixel = (pixel_x, pixel_y)
            old_pixel = (gcp.pixel_x, gcp.pixel_y)
            lng = feature['geometry']['coordinates'][0]
            lat = feature['geometry']['coordinates'][1]

            new_geom = Point(lat, lng, srid=4326)

            # only update the point if one of its coordinate pairs have changed,
            # this also triggered when new GCPs have None for pixels and geom.
            if new_pixel != old_pixel or not new_geom.equals(gcp.geom):
                gcp.pixel_x = new_pixel[0]
                gcp.pixel_y = new_pixel[1]
                gcp.geom = new_geom
                gcp.last_modified_by = user
                gcp.save()
                print("coordinates saved/updated")
            else:
                print("gcp coordinates unchanged, no save made")

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
        thumb = create_thumbnail(self.layer, overwrite=True)
        self.layer.thumbnail_url = thumb
        self.layer.save()

class MaskSession(models.Model):

    class Meta:
        verbose_name = "Mask Session"
        verbose_name_plural = "Mask Sessions"

    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    polygon = models.PolygonField(null=True, blank=True, srid=3857)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        null=False,
        blank=False)
    note = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )

    def run(self):

        ## first get the related Document so the statuses can be managed
        ct = ContentType.objects.get(app_label="layers", model="layer")
        document = GeoreferencedDocumentLink.objects.get(
            content_type=ct,
            object_id=self.layer.pk,
        ).document

        tkm = TKeywordManager()
        tkm.set_status(self.layer, "trimming")
        tkm.set_status(document, "trimming")

        # create/update a LayerMask for this layer and apply it as style
        if self.polygon is not None:

            try:
                mask = LayerMask.objects.get(layer=self.layer)
                mask.polygon = self.polygon
                mask.save()
            except LayerMask.DoesNotExist:
                mask = LayerMask.objects.create(
                    layer=self.layer,
                    polygon=self.polygon,
                )
            mask.apply_mask()

            tkm.set_status(self.layer, "trimmed")
            tkm.set_status(document, "trimmed")

        # if there is no polygon, then clean up old mask styles and reset the
        # default style to original (if needed)
        else:

            # delete the LayerMask object
            LayerMask.objects.filter(layer=self.layer).delete()

            # delete the existing trim style in Geoserver if necessary
            cat = get_gs_catalog()
            trim_style_name = f"{self.layer.name}_trim"
            gs_trim_style = cat.get_style(trim_style_name, workspace="geonode")
            if gs_trim_style is not None:
                cat.delete(gs_trim_style, recurse=True)

            # delete the existing trimmed style in GeoNode
            Style.objects.filter(name=trim_style_name).delete()

            # set the full style back to the default in GeoNode
            gn_full_style = Style.objects.get(name=self.layer.name)
            self.layer.default_style = gn_full_style
            self.layer.save()

            # update thumbnail
            thumb = create_thumbnail(self.layer, overwrite=True)
            self.layer.thumbnail_url = thumb
            self.layer.save()

            tkm.set_status(self.layer, "georeferenced")
            tkm.set_status(document, "georeferenced")

    def serialize(self):
        vertex_ct = 0
        if self.polygon is not None:
            vertex_ct = len(self.polygon.coords[0]) - 1
        return {
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
            },
            "date": (self.created.month, self.created.day, self.created.year),
            "date_str": self.created.strftime("%Y-%m-%d"),
            "datetime": self.created.strftime("%Y-%m-%d - %H:%M"),
            "vertex_ct": vertex_ct,
        }

def get_default_session_data(session_type):
    """Return a dict of the keys/types for a sessions's data field.
    Also used for type-checking during validation."""

    if session_type == "p":
        return {
            "split_needed": bool(),
            "cutlines": list(),
            "divisions": list(),
        }
    elif session_type == "g":
        return {
            "gcps": dict(),
            "transformation": str(),
            "epsg": int(),
        }
    elif session_type == "t":
        return {
            "mask_ewkt": str(),
        }
    else:
        raise Exception(f"Invalid session type: {session_type}")

class PrepSessionManager(models.Manager):

    _type = 'p'

    def get_queryset(self):
        return super(PrepSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
            'data': get_default_session_data(self._type),
        })
        return super(PrepSessionManager, self).create(**kwargs)

class GeorefSessionManager(models.Manager):

    _type = 'g'

    def get_queryset(self):
        return super(GeorefSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
            'data': get_default_session_data(self._type),
        })
        return super(GeorefSessionManager, self).create(**kwargs)

class TrimSessionManager(models.Manager):

    _type = 't'

    def get_queryset(self):
        return super(TrimSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
            'data': get_default_session_data(self._type),
        })
        return super(TrimSessionManager, self).create(**kwargs)

SESSION_TYPES = (
    ('p', 'Preparation'),
    ('g', 'Georeference'),
    ('t', 'Trim'),
)
SESSION_STAGES = (
    ('input', 'input'),
    ('processing', 'processing'),
    ('finished', 'finished'),
)

class SessionBase(models.Model):

    type = models.CharField(
        max_length=1,
        choices=SESSION_TYPES,
        blank=True,
    )
    stage = models.CharField(
        max_length=11,
        choices=SESSION_STAGES,
        default="input",
    )
    status = models.CharField(
        max_length=50,
        default="getting user input",
    )
    document = models.ForeignKey(
        Document,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    layer = models.ForeignKey(
        Layer,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    data = JSONField(
        default=dict,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    date_created = models.DateTimeField(
        default=timezone.now,
    )
    date_modified = models.DateTimeField(
        default=timezone.now,
    )
    date_run = models.DateTimeField(
        blank=True,
        null=True,
    )
    note = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )

    def start(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def run(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def cancel(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def undo(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def serialize(self):

        # handle the non- js-serializable attributes
        doc_id, layer_alt, d_create, d_mod, d_run = None, None, None, None, None
        d_run_d, d_run_t = None, None
        if self.document:
            doc_id = self.document.pk
        if self.layer:
            layer_alt = self.layer.alternate
        if self.date_created:
            d_create = self.date_created.strftime("%Y-%m-%d - %H:%M")
        if self.date_modified:
            d_mod = self.date_modified.strftime("%Y-%m-%d - %H:%M")
        if self.date_run:
            d_run = self.date_run.strftime("%Y-%m-%d - %H:%M")
            d_run_d = self.date_run.strftime("%Y-%m-%d")
            d_run_t = self.date_run.strftime("%H:%M")

        return {
            "id": self.pk,
            "type": self.get_type_display(),
            "document": doc_id,
            "layer": layer_alt,
            "stage": self.stage,
            "status": self.status,
            "note": self.note,
            "data": self.data,
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
            },
            "date_created": d_create,
            "date_modified": d_mod,
            "date_run": d_run,
            "date_run_date": d_run_d,
            "date_run_time": d_run_t,
        }

    def update_stage(self, stage, save=True):
        self.stage = stage
        logger.info(f"{self.__str__()} | stage: {self.stage}")
        if save:
            self.save(update_fields=["stage"])

    def update_status(self, status, save=True):
        self.status = status
        logger.info(f"{self.__str__()} | status: {self.status}")
        if save:
            self.save(update_fields=["status"])

    def get_document_for_layer(self):

        if self.layer is None:
            return None
        ct = ContentType.objects.get(app_label="layers", model="layer")
        try:
            document = GeoreferencedDocumentLink.objects.get(
                content_type=ct,
                object_id=self.layer.pk,
            ).document
            return document
        except Document.DoesNotExist:
            return None

    def validate_data(self):
        """Compares the contents of the session's data field with the
        appropriate set of keys and types for this session type. Does not
        validate data value content like GeoJSON, etc."""

        for k, v in self.data.items():
            lookup = get_default_session_data(self.type)
            if k not in lookup.keys():
                raise KeyError(f"{self.__str__()} data | Invalid key: {k}")
            if not isinstance(v, type(lookup[k])):
                raise TypeError(f"{self.__str__()} data | Invalid type: {k} is {type(v)}, must be {type(lookup[k])}")

    def save(self, *args, **kwargs):
        self.validate_data()
        self.date_modified = timezone.now()
        return super(SessionBase, self).save(*args, **kwargs)


class PrepSession(SessionBase):
    objects = PrepSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Preparation Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = "   Preparation Sessions"

    def __str__(self):
        return f"Preparation Session ({self.pk})"

    @property
    def georeferenced_downstream(self):
        """Returns True if the related document or its children (if it
        has been split) have already been georeferenced."""

        if self.data["split_needed"] is True:
            docs_to_check = self.get_children()
        else:
            docs_to_check = [self.document]

        tkm = TKeywordManager()
        return any([tkm.is_georeferenced(d) for d in docs_to_check])

    def get_children(self):
        """Returns a list of all the child documents that have been created
        by a split operation from this session."""

        ct = ContentType.objects.get(app_label="documents", model="document")
        child_ids = SplitDocumentLink.objects.filter(
            document=self.document,
            content_type=ct,
        ).values_list("object_id", flat=True)
        return list(Document.objects.filter(pk__in=child_ids))

    def start(self):
        tkm = TKeywordManager()
        tkm.set_status(self.document, "splitting")

    def run(self):
        """
        Runs the document split process based on prestored segmentation info
        that has been generated for this document. New Documents are made for
        each child image, SplitDocumentLinks are created to link this parent
        Document with its children. The parent document is also marked as
        metadata_only so that it no longer shows up in the search page lists.
        """

        if self.stage == "processing" or self.stage == "finished":
            logger.warn(f"{self.__str__()} | abort run: session is already processing or finished.")
            return

        self.date_run = timezone.now()

        self.update_stage("processing")
        tkm = TKeywordManager()
        tkm.set_status(self.document, "splitting")

        if self.data['split_needed'] is False:
            tkm.set_status(self.document, "prepared")
            self.document.metadata_only = False
            self.document.save()
        else:
            self.update_status("splitting document image")
            s = Splitter(image_file=self.document.doc_file.path)
            self.data['divisions'] = s.generate_divisions(self.data['cutlines'])
            new_images = s.split_image()

            for n, file_path in enumerate(new_images, start=1):
                self.update_status(f"creating new document [{n}]")
                fname = os.path.basename(file_path)
                new_doc = Document.objects.get(pk=self.document.pk)
                new_doc.pk = None
                new_doc.id = None
                new_doc.uuid = None
                new_doc.thumbnail_url = None
                new_doc.metadata_only = False
                new_doc.title = f"{self.document.title} [{n}]"
                with open(file_path, "rb") as openf:
                    new_doc.doc_file.save(fname, File(openf))
                new_doc.save()

                os.remove(file_path)

                ct = ContentType.objects.get(app_label="documents", model="document")
                SplitDocumentLink.objects.create(
                    document=self.document,
                    content_type=ct,
                    object_id=new_doc.pk,
                )

                for r in self.document.regions.all():
                    new_doc.regions.add(r)
                tkm.set_status(new_doc, "prepared")

            if len(new_images) > 1:
                self.document.metadata_only = True
                self.document.save()

            tkm.set_status(self.document, "split")

        self.update_status("success", save=False)
        self.update_stage("finished", save=False)
        self.save()
        return

    def undo(self):
        """Reverses the effects of this preparation session: remove child documents and
        links to them, then delete this session."""

        # first check to make sure this determination can be reversed.
        if self.georeferenced_downstream is True:
            logger.warn(f"Removing SplitEvaluation {self.pk} even though downstream georeferencing has occurred.")

        # if a split was made, remove all descendant documents before deleting
        for child in self.get_children():
            child.delete()

        SplitDocumentLink.objects.filter(document=self.document).delete()

        TKeywordManager().set_status(self.document, "unprepared")
        self.document.metadata_only = False
        self.document.save()
        self.delete()

    def generate_final_status_note(self):

        if self.data['split_needed'] is False:
            n = "no split needed"
        else:
            pks = [str(i.pk) for i in self.get_children()]
            n = f"split into {len(pks)} new docs ({', '.join(pks)})"
        return n

    def save(self, *args, **kwargs):
        self.type = 'p'
        if not self.document:
            logger.warn(f"{self.__str__()} has no Document.")
        if not self.pk:
            self.data = get_default_session_data(self.type)
        if self.stage == "finished":
            self.note = self.generate_final_status_note()
        return super(PrepSession, self).save(*args, **kwargs)

    def serialize(self):

        if self.date_run:
            date = (self.date_run.month, self.date_run.day, self.date_run.year)
            date_str = self.date_run.strftime("%Y-%m-%d")
            datetime = self.date_run.strftime("%Y-%m-%d - %H:%M")
        else:
            date = (None, None, None)
            date_str = ""
            datetime = ""

        return {
            "allow_reset": not self.georeferenced_downstream,
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
            },
            "date": date,
            "date_str": date_str,
            "datetime": datetime,
            "split_needed": self.data['split_needed'],
            "divisions_ct": len(self.get_children()),
        }


class GeorefSession(SessionBase):
    objects = GeorefSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Georeference Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = "  Georeference Sessions"

    def __str__(self):
        return f"Georeference Session ({self.pk})"

    def start(self):
        tkm = TKeywordManager()
        tkm.set_status(self.document, "georeferencing")

    def run(self):

        tkm = TKeywordManager()
        tkm.set_status(self.document, "georeferencing")

        self.date_run = timezone.now()
        self.update_stage("processing", save=False)
        self.update_status("initializing georeferencer", save=False)
        self.save()

        try:
            g = Georeferencer(
                transformation=self.data['transformation'],
                epsg_code=self.data['epsg'],
            )
            g.load_gcps_from_geojson(self.data['gcps'])
        except Exception as e:
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            # revert to previous tkeyword status
            tkm.set_status(self.document, "prepared")
            return None
        self.update_status("warping")
        try:
            out_path = g.make_tif(self.document.doc_file.path)
        except Exception as e:
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            # revert to previous tkeyword status
            tkm.set_status(self.document, "prepared")
            return None

        # self.transformation_used = g.transformation["id"]
        self.update_status("creating layer")

        ## need to remove commas from the titles, otherwise the layer will not
        ## be valid in the catalog list when trying to add it to a Map. the 
        ## message in the catalog will read "Missing OGC reference metadata".
        title = self.document.title.replace(",", " -")

        ## first look to see if there is a layer alreaded linked to this document.
        ## this would indicate that it has already been georeferenced, and in this
        ## case the existing layer should be overwritten.
        existing_layer = None
        try:
            link = GeoreferencedDocumentLink.objects.get(document=self.document)
            existing_layer = Layer.objects.get(pk=link.object_id)
        except (GeoreferencedDocumentLink.DoesNotExist, Layer.DoesNotExist):
            pass

        ## create the layer, passing in the existing_layer if present
        layer = file_upload(
            out_path,
            layer=existing_layer,
            overwrite=True,
            title=title,
            user=self.user,
        )

        ## if there was no existing layer, create a new link between the
        ## document and the new layer
        if existing_layer is None:
            ct = ContentType.objects.get(app_label="layers", model="layer")
            GeoreferencedDocumentLink.objects.create(
                document=self.document,
                content_type=ct,
                object_id=layer.pk,
            )

            # set attributes in the layer straight from the document
            for keyword in self.document.keywords.all():
                layer.keywords.add(keyword)
            for region in self.document.regions.all():
                layer.regions.add(region)
            Layer.objects.filter(pk=layer.pk).update(
                date=self.document.date,
                abstract=self.document.abstract,
                category=self.document.category,
                license=self.document.license,
                restriction_code_type=self.document.restriction_code_type,
                attribution=self.document.attribution,
            )

        ## if there was an existing layer that's been overwritten, regenerate thumb.
        else:
            self.update_status("regenerating thumbnail")
            thumb = create_thumbnail(layer, overwrite=True)
            Layer.objects.filter(pk=layer.pk).update(thumbnail_url=thumb)

        self.layer = layer
        self.update_status("saving control points")

        # save the successful gcps to the canonical GCPGroup for the document
        GCPGroup().save_from_geojson(
            self.data['gcps'],
            self.document,
            self.data['transformation'],
        )

        tkm.set_status(self.document, "georeferenced")
        tkm.set_status(layer, "georeferenced")

        self.update_stage("finished", save=False)
        self.update_status("success", save=False)
        self.save()

        return layer

    def undo(self, undo_all=False):
        """
        Remove this GeorefSession and revert the Document/Layer to previous
        state. If undo_all is True, revert all sessions (clean slate).

        If this is the only GeorefSession on the Document, or if undo_all
        is True, then remove the Layer and set the document to "prepared".
        Otherwise, reapply the latest session after removing this one.

        If undo_all is False and this isn't the most recent session on
        the Document, abort the undo operation.
        """

        tkm = TKeywordManager()

        ##  get all of the sessions for this document, ordered so most recent is first
        sessions = GeorefSession.objects.filter(document=self.document).order_by("-date_run")
        if self != list(sessions)[0] and undo_all is False:
            logger.warn(f"{self.__str__()} | can't undo this session, it's not the latest one.")
            return
        else:
            logger.info(f"{self.__str__()} | undo session (undo_all = {undo_all})")

        ## If this is the only session, or undo_all is True then wipe the slate clean
        if sessions.count() == 1 or undo_all is True:

            ## find and delete the Layer
            layer = None
            try:
                link = GeoreferencedDocumentLink.objects.get(document=self.id)
                layer = Layer.objects.get(id=link.object_id)
            except (GeoreferencedDocumentLink.DoesNotExist, Layer.DoesNotExist):
                pass

            if layer is None:
                logger.debug(f"{self.__str__()} | no Layer to delete")
            else:
                logger.debug(f"{self.__str__()} | delete Layer: {layer}")
                layer.delete()

            ## remove the link between the Document and the Layer
            try:
                GeoreferencedDocumentLink.objects.get(document=self.document.id).delete()
                logger.debug(f"{self.__str__()} | delete GeoreferencedDocumentLink")
            except GeoreferencedDocumentLink.DoesNotExist:
                logger.debug(f"{self.__str__()} | no GeoreferencedDocumentLink to delete")

            ## remove all sessions
            logger.info(f"{self.__str__()} | delete all sessions: {[s.pk for s in sessions]}")
            sessions.delete()
            GCPGroup.objects.filter(document=self.document).delete()
            tkm.set_status(self.document, "prepared")

        ## otherwise delete this session and then re-run the latest one before it.
        else:
            logger.info(f"{self.__str__()} | deleted")
            docid = self.document.pk
            self.delete()

            #reaquire sessions, seems like it may be necessary??
            sessions = GeorefSession.objects.filter(document_id=docid).order_by("-date_run")
            latest = list(sessions)[0]
            logger.info(f"{latest.__str__()} | re-run session")
            latest.run()

            # finally, for all previous sessions reset the newly re-created layer
            for s in sessions:
                s.layer = latest.layer
                s.save()

    def generate_final_status_note(self):

        try:
            gcp_ct = len(self.data['gcps']['features'])
            n = f"{gcp_ct} GCPs used"
        except KeyError:
            n = f"error reading GCPs"
        return n

    def save(self, *args, **kwargs):
        self.type = 'g'
        if not self.document:
            logger.warn(f"{self.__str__()} has no Document.")
        if not self.pk:
            self.data = get_default_session_data(self.type)
        if self.stage == "finished" and self.status == "success":
            self.note = self.generate_final_status_note()
        return super(GeorefSession, self).save(*args, **kwargs)


class TrimSession(SessionBase):
    objects = TrimSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Trim Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = " Trim Sessions"

    def __str__(self):
        return f"Trim Session ({self.pk})"

    def start(self):
        tkm = TKeywordManager()
        tkm.set_status(self.layer, "trimming")

    def run(self):

        self.update_stage("processing", save=False)
        self.date_run = timezone.now()
        self.save()
        tkm = TKeywordManager()
        tkm.set_status(self.layer, "trimming")

        document = self.get_document_for_layer()
        if document is not None:
            tkm.set_status(document, "trimming")

        # create/update a LayerMask for this layer and apply it as style
        if self.data['mask_ewkt']:
            
            mask = GEOSGeometry(self.data['mask_ewkt'])
            lm, created = LayerMask.objects.get_or_create(
                layer=self.layer,
                defaults={"polygon": mask}
            )
            if not created:
                lm.polygon = mask
                lm.save()
            lm.apply_mask()

            tkm.set_status(self.layer, "trimmed")
            if document is not None:
                tkm.set_status(document, "trimmed")

        self.update_stage("finished", save=False)
        self.update_status("success", save=False)
        self.save()

    def undo(self):

        tkm = TKeywordManager()
        tkm.set_status(self.layer, "georeferenced")
        document = self.get_document_for_layer()

        if document is not None:
            tkm.set_status(document, "georeferenced")

        LayerMask.objects.filter(layer=self.layer).delete()

        self.set_status("unapplied")

    def save(self, *args, **kwargs):
        self.type = 't'
        if not self.layer:
            logger.warn(f"{self.__str__()} has no Layer.")
        if not self.pk:
            self.data = get_default_session_data(self.type)
        return super(TrimSession, self).save(*args, **kwargs)
