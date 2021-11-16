import logging
from PIL import Image

from django.contrib.gis.geos import Polygon
from django.shortcuts import get_object_or_404

from geonode.documents.models import Document
from geonode.layers.models import Layer

from .models import (
    GeoreferencedDocumentLink,
    SplitDocumentLink,
    LayerMask,
    Segmentation,
    SplitSession,
    GeoreferenceSession,
    GCPGroup,
)
from .utils import (
    full_reverse,
    get_status,
    mapserver_add_layer,
    mapserver_remove_layer,
)

logger = logging.getLogger(__name__)

class DocumentProxy(object):

    def __init__(self, docid, raise_404_on_error=False):

        if raise_404_on_error:
            document = get_object_or_404(Document, pk=docid)
        else:
            document = Document.objects.get(pk=docid)

        # transfer relevant Document attributes to this object.
        # it's a bit cleaner to be explicit here than just use
        # self.document = document and then self.document.id over and over...
        self.id = document.id
        self.title = document.title
        self.tkeywords = list(document.tkeywords.all())
        self.regions = list(document.regions.all())
        self.doc_file = document.doc_file

        self.urls = {
            "thumbnail": document.thumbnail_url,
            "detail": document.detail_url,
            "image": full_reverse('document_download', args=(document.id,)),
            "split": full_reverse("split_view", args=(document.id, )),
            "georeference": full_reverse("georeference_view", args=(document.id, )),
            "progress_page": full_reverse("georeference_summary", args=(document.id, )),
        }

        self.resource = document

    @property
    def status(self):
        return get_status(self.resource)

    @property
    def child_docs(self):
        links = SplitDocumentLink.objects.filter(document=self.id)
        return [DocumentProxy(i.object_id) for i in links]

    @property
    def parent_doc(self):
        try:
            link = SplitDocumentLink.objects.get(object_id=self.id)
            parent = DocumentProxy(link.document.id)
        except SplitDocumentLink.DoesNotExist:
            parent = None
        return parent

    @property
    def split_session(self):
        sesh = SplitSession.objects.filter(document=self.resource)
        if len(sesh) == 0:
            return None
        else:
            return sesh[0]
    
    @property
    def image_size(self):
        return Image.open(self.doc_file).size

    @property
    def segmentation(self):
        try:
            return Segmentation.objects.get(document=self.id)
        except Segmentation.DoesNotExist:
            return None

    @property
    def segments(self):
        segmentation = self.segmentation
        if segmentation is not None:
            return segmentation.segments
        else:
            None
    
    @property
    def cutlines(self):
        segmentation = self.segmentation
        if segmentation is not None:
            return segmentation.cutlines
        else:
            None

    @property
    def gcp_group(self):
        try:
            return GCPGroup.objects.get(document=self.id)
        except GCPGroup.DoesNotExist:
            return None

    @property
    def gcps_geojson(self):
        gcp_group = self.gcp_group
        if gcp_group is not None:
            return gcp_group.as_geojson
        else:
            None

    @property
    def transformation(self):
        gcp_group = self.gcp_group
        if gcp_group is not None:
            return gcp_group.transformation
        else:
            None

    def get_document(self):
        return Document.objects.get(id=self.id)

    def get_layer(self):

        try:
            link = GeoreferencedDocumentLink.objects.get(document=self.id)
            layer = Layer.objects.get(id=link.object_id)
        except GeoreferencedDocumentLink.DoesNotExist:
            layer = None
        return layer

    def get_layer_proxy(self):

        layer = self.get_layer()
        if layer is not None:
            layer = LayerProxy(layer.alternate)
        return layer

    def get_layer_json(self):

        layer_proxy = self.get_layer_proxy()
        if layer_proxy is not None:
            return layer_proxy.serialize()
        else:
            return None
    
    def get_layer_urls(self):
        layer_urls = {}
        layer_proxy = self.get_layer_proxy()
        if layer_proxy is not None:
            layer_urls = layer_proxy.urls
        return {
            "layer_detail": layer_urls.get("detail", "")
        }

    def get_split_summary(self):

        if self.parent_doc is not None:
            sesh = self.parent_doc.split_session
        else:
            sesh = self.split_session

        # this would be an unevaluated document
        if sesh is None:
            return None
        
        sesh_info = sesh.serialize()

        parent_json = None
        if self.parent_doc:
            parent_json = self.parent_doc.serialize()
        child_json = [i.serialize() for i in self.child_docs]

        sesh_info.update({
            "parent_doc": parent_json,
            "child_docs": child_json,
        })

        return sesh_info

    def get_georeference_summary(self):

        summary = {
            "sessions": []
        }

        layer = self.get_layer_proxy()

        # this would the document is not yet georeferenced
        if layer is None:
            return summary

        seshes = GeoreferenceSession.objects.filter(document=self.id).order_by("created")
        for sesh in seshes:
            summary["sessions"].append(sesh.serialize())

        return summary

    def get_best_region_extent(self):
        """
        Gets the extent of the smallext region attached to this document.
        Could be improved to use the heirarchical region levels. Best would
        be an aggregation of all regions on the highest level (i.e. two
        adjacent towns).
        """
        use_polygon = Polygon.from_bbox((-180, -90, 180, 90))
        for region in self.resource.regions.all():
            polygon = Polygon.from_bbox(region.bbox[:4])
            if polygon.area < use_polygon.area:
                use_polygon = polygon
        region_extent = use_polygon.extent
        return region_extent
    
    def get_extended_urls(self):
        urls = self.urls
        urls.update(self.get_layer_urls())
        return urls

    def add_mapserver_layer(self):
        ms_layer = mapserver_add_layer(self.doc_file.path)
        return ms_layer

    def remove_mapserver_layer(self):
        mapserver_remove_layer(self.doc_file.path)

    def serialize(self):

        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "urls": self.get_extended_urls(),
        }

class LayerProxy(object):
    
    def __init__(self, identifier, raise_404_on_error=False):
        # this is a little weird, but allow instantiation via id or
        # via alterate, base determination on whether the identifier
        # is an integer or a string
        if str(identifier).isdigit():
            query = {"id": identifier}
        else:
            query = {"alternate": identifier}
        if raise_404_on_error:
            layer = get_object_or_404(Layer, **query)
        else:
            layer = Layer.objects.get(**query)

        self.id = layer.id
        self.alternate = layer.alternate
        self.title = layer.title
        self.name = layer.name
        self.workspace = layer.workspace
        self.geoserver_id = f"{layer.workspace}:{layer.name}"
        self.extent = layer.ll_bbox_polygon.extent
        self.tkeywords = list(layer.tkeywords.all())
        self.regions = list(layer.regions.all())

        self.urls = {
            "thumbnail": layer.thumbnail_url,
            "detail": full_reverse("layer_detail", args=(layer.alternate, )),
            "trim": full_reverse("trim_view", args=(layer.alternate, )),
        }

        self.resource = layer

    @property
    def status(self):
        return get_status(self.resource)

    @property
    def mask(self):
        try:
            return LayerMask.objects.get(layer_id=self.id)
        except LayerMask.DoesNotExist:
            return None
    
    @property
    def mask_coords(self):

        coords = []
        mask = self.mask
        if mask is not None:
            if mask.polygon:
                coords = mask.polygon.coords[0]
        return coords

    def get_layer(self):
        return Layer.objects.get(id=self.id)

    def get_document(self):

        try:
            link = GeoreferencedDocumentLink.objects.get(object_id=self.id)
            document = link.document
        except GeoreferencedDocumentLink.DoesNotExist:
            document = None
        return document

    def get_document_proxy(self):
        document = self.get_document()
        if document is not None:
            document = DocumentProxy(document.id)
        return document

    def get_document_urls(self):

        doc_urls = {}
        doc_proxy = self.get_document_proxy()
        if doc_proxy is not None:
            doc_urls = doc_proxy.urls
        return {
            "georeference": doc_urls.get("georeference", ""),
            "progress_page": doc_urls.get("progress_page", ""),
            "document_detail": doc_urls.get("detail", ""),
        }
    
    def get_mask_coords(self):

        mask, created = LayerMask.objects.get_or_create(layer_id=self.id)
        if mask.polygon:
            coords = mask.polygon.coords[0]
        else:
            coords = []
        return coords
    
    def get_extended_urls(self):

        urls = self.urls
        urls.update(self.get_document_urls())
        return urls
    
    def serialize(self):

        return {
            "alternate": self.alternate,
            "title": self.title,
            "name": self.name,
            "workspace": self.workspace,
            "geoserver_id": self.geoserver_id,
            "extent": self.extent,
            "status": self.status,
            "urls": self.get_extended_urls(),
        }
