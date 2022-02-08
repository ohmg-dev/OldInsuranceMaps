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
    SplitEvaluation,
    GeoreferenceSession,
    MaskSession,
    GCPGroup,
)
from .utils import (
    full_reverse,
    TKeywordManager,
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
            "detail": document.detail_url + "#georeference",
            "image": full_reverse('document_download', args=(document.id,)),
            "split": full_reverse("split_view", args=(document.id, )),
            "georeference": full_reverse("georeference_view", args=(document.id, )),
            "progress_page": document.detail_url + "#georeference",
        }

        self.resource = document

    @property
    def status(self):
        return TKeywordManager().get_status(self.resource)

    @property
    def split_evaluation(self):
        try:
            return SplitEvaluation.objects.get(document=self.resource)
        except SplitEvaluation.DoesNotExist:
            return None

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
    def image_size(self):
        return Image.open(self.doc_file).size

    @property
    def cutlines(self):
        cutlines = []
        if self.split_evaluation is not None:
            if self.split_evaluation.cutlines is not None:
                cutlines = self.split_evaluation.cutlines
        return cutlines

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
            return None

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
            "layer_detail": layer_urls.get("detail", ""),
            "layer_trim": layer_urls.get("trim", ""),
        }

    def get_split_summary(self):

        if self.parent_doc is not None:
            evaluation = self.parent_doc.split_evaluation
        else:
            evaluation = self.split_evaluation
        # this would be an unevaluated document
        if evaluation is None:
            return None

        info = evaluation.serialize()

        parent_json = None
        if self.parent_doc:
            parent_json = self.parent_doc.serialize()
        child_json = [i.serialize() for i in self.child_docs]

        info.update({
            "parent_doc": parent_json,
            "child_docs": child_json,
        })

        return info

    def get_georeference_summary(self):

        sessions = self.get_georeference_sessions(serialized=True)

        return {
            "sessions": sessions,
            "gcp_geojson": self.gcps_geojson,
            "transformation": self.transformation,
        }

    def get_georeference_sessions(self, serialized=False):
        sessions = GeoreferenceSession.objects.filter(document=self.id).order_by("created")
        if serialized is True:
            return [i.serialize() for i in sessions]
        else:
            return sessions

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

    def serialize(self):

        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "urls": self.get_extended_urls(),
            "split_evaluation": self.split_evaluation.serialize() if \
                self.split_evaluation else None,
        }

    def get_actions(self):
        actions = []

        if self.parent_doc is not None:
            sesh = self.parent_doc.split_evaluation.serialize()
            split_action = {
                "type": "split",
                "user": sesh['user'],
                "date": sesh['date_str'],
                "datetime": sesh['datetime'],
                "details": "split from " + self.parent_doc.title,
            }
        elif self.split_evaluation is not None:
            sesh = self.split_evaluation.serialize()
            if sesh['split_needed'] is False:
                details = "no split needed"
            else:
                details = f"{sesh['divisions_ct']} segments"
            split_action = {
                "type": "split",
                "user": sesh['user'],
                "date": sesh['date_str'],
                "datetime": sesh['datetime'],
                "details": details,
            }
        else:
            return []
        actions.append(split_action)

        for sesh in self.get_georeference_sessions(serialized=True):
            actions.append({
                "type": "georeference",
                "user": sesh['user'],
                "date": sesh['date_str'],
                "datetime": sesh['datetime'],
                "details": f"{sesh['gcps_ct']} GCPs",
            })
        return actions

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
        return TKeywordManager().get_status(self.resource)

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

    def get_extended_urls(self):

        urls = self.urls
        urls.update(self.get_document_urls())
        return urls

    def get_mask_sessions(self, serialized=False):
        sessions = MaskSession.objects.filter(layer=self.id).order_by("created")
        if serialized is True:
            return [i.serialize() for i in sessions]
        else:
            return sessions
    
    def get_action_history(self):
        actions = []
        for sesh in self.get_mask_sessions(serialized=True):
            actions.append({
                "type": "trim",
                "date": sesh['date_str'],
                "datetime": sesh['datetime'],
                "user": sesh['user'],
                "details": sesh['vertex_ct'],
            })
        return actions
    
    def get_trim_summary(self):

        return {
            "sessions": self.get_mask_sessions(serialized=True)
        }

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

def get_georeferencing_summary(resourceid):
    """Used in a context processor or view to generate all information
    needed for the georeference info panel in the Document or Layer
    detail pages."""

    if str(resourceid).isdigit():
        doc_proxy = DocumentProxy(resourceid)
        layer_proxy = doc_proxy.get_layer_proxy()
        resource_type = "document"
    else:
        layer_proxy = LayerProxy(resourceid)
        doc_proxy = layer_proxy.get_document_proxy()
        resource_type = "layer"

    actions = doc_proxy.get_actions()
    urls = {
        "refresh": full_reverse('summary_json', args=(doc_proxy.id,)),
        "document_detail": doc_proxy.urls['detail'],
        "layer_detail": "",
        "split": doc_proxy.urls['split'],
        "georeference": doc_proxy.urls['georeference'],
        "trim": "",
    }
    trim_summary = {
        "sessions": []
    }
    layer_alternate = ""

    if layer_proxy is not None:
        layer_alternate = layer_proxy.alternate
        urls['layer_detail'] = layer_proxy.urls['detail']
        urls['trim'] = layer_proxy.urls['trim']
        trim_summary = layer_proxy.get_trim_summary()
        actions += layer_proxy.get_action_history()

    sorted_actions = sorted(actions, key = lambda e: e["datetime"])

    context = {
        "STATUS": doc_proxy.status,
        "RESOURCE_TYPE": resource_type,
        "DOCUMENT_ID": doc_proxy.id,
        "LAYER_ALTERNATE": layer_alternate,
        "URLS": urls,
        "SPLIT_SUMMARY": doc_proxy.get_split_summary(),
        "GEOREFERENCE_SUMMARY": doc_proxy.get_georeference_summary(),
        "TRIM_SUMMARY": trim_summary,
        "ACTION_HISTORY": sorted_actions,
    }
    return context

def get_search_item_info(resource_type, resource_id):
    """Returns a set of georeferencing-related links and status
    for use in middleware that augments the search result items in
    the documents, layers, and haystack search pages."""

    # set default status
    status = "n/a"
    # create full suite of links, without any urls
    linkset = {
        "overview": {
            "title": "Progress Overview",
            "icon": "fa-list-ol",
            "url": "",
        },
        "prepare": {
            "title": "Prepare Document",
            "icon": "fa-cut",
            "url": "",
        },
        "georeference": {
            "title": "Georeference Document",
            "icon": "fa-map-pin",
            "url": "",
        },
        "trim": {
            "title": "Trim Layer",
            "icon": "fa-crop",
            "url": "",
        },
        "related": {
            "title": "",
            "icon": "fa-exchange",
            "url": "",
        },
    }

    proxy = None
    if resource_type == "document":
        proxy = DocumentProxy(resource_id)
    if resource_type == "layer":
        proxy = LayerProxy(resource_id)

    if proxy is not None:
        status = proxy.status
        proxy_urls = proxy.get_extended_urls()

        linkset["overview"]["url"] = proxy_urls['detail']
        if status == "unprepared":
            linkset["prepare"]["url"] = proxy_urls['split']
        if status == "prepared":
            linkset["georeference"]["url"] = proxy_urls['georeference']
        if status == "georeferenced" or status == "trimmed":
            linkset["georeference"]["title"] = "Edit Georeferencing"
            linkset["georeference"]["url"] = proxy_urls['georeference']
            if resource_type == "layer":
                linkset["trim"]["url"] = proxy_urls['trim']
                linkset["related"]["title"] = "Jump to source Document"
                linkset["related"]["url"] = proxy_urls['document_detail']
            if resource_type == "document":
                linkset["related"]["title"] = "Jump to georeferenced Layer"
                linkset["trim"]["url"] = proxy_urls['layer_trim']
                linkset["related"]["url"] = proxy_urls['layer_detail']

    return {
        'georeference_links': list(linkset.values()),
        'georeference_status': status,
    }
