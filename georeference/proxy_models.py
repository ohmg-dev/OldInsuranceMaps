
import os
import logging
from PIL import Image
from itertools import chain
from datetime import timedelta

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.shortcuts import get_object_or_404
from django.utils import timezone

from geonode.documents.models import Document
from geonode.layers.models import Layer, LayerFile

from georeference.models.resources import (
    GeoreferencedDocumentLink,
    SplitDocumentLink,
    LayerMask,
    GCPGroup,
)
from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
    TrimSession,
)
from georeference.utils import (
    full_reverse,
    TKeywordManager,
)

logger = logging.getLogger(__name__)

class SessionLock(object):
    """
    Defines a Lock object that can be used for resources.
    """

    def __init__(self, doc_proxy=None, layer_proxy=None):

        self.enabled = False
        self.type = ""
        self.stage = ""
        self.username = ""
        self.timeleft = None

        if doc_proxy is not None:
            if doc_proxy.preparation_session is not None:
                if doc_proxy.preparation_session.stage == "input":
                    self.set_from_session(doc_proxy.preparation_session)
            for gs in doc_proxy.georeference_sessions:
                if gs.stage == "input":
                    self.set_from_session(gs)

        elif layer_proxy is not None:
            for ts in layer_proxy.trim_sessions:
                if ts.stage == "input":
                    self.set_from_session(ts)

    @property
    def as_dict(self):

        if self.timeleft is not None:
            if self.timeleft.seconds == 0:
                timeleft_str = "0m 0s"
            else:
                hours, remainder = divmod(self.timeleft.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                hrs_int = int(hours)
                min_int = str(int(minutes))
                sec_int = str(int(seconds))
                timeleft_str = f"{min_int}m {sec_int}s"
                if hrs_int != 0:
                    timeleft_str = f"{hrs_int}h " + timeleft_str
        else:
            timeleft_str = "n/a"

        return {
            "enabled": self.enabled,
            "type": self.type,
            "stage": self.stage,
            "username": self.username,
            "timeleft": timeleft_str,
        }

    def set_from_session(self, session):
        self.enabled = True
        self.type = session.type
        self.stage = session.stage
        if session.user is not None:
            self.username = session.user.username
        allowed_length = settings.GEOREFERENCE_SESSION_LENGTH
        cutoff = timezone.now() - timedelta(seconds=allowed_length)
        timeleft = session.date_created - cutoff
        if timeleft < timedelta():
            timeleft = timedelta()
        self.timeleft = timeleft

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
    def preparation_session(self):
        try:
            return PrepSession.objects.get(document=self.resource)
        except PrepSession.DoesNotExist:
            if self.parent_doc is not None:
                return self.parent_doc.preparation_session
            else:
                return None
        except PrepSession.MultipleObjectsReturned:
            logger.warn(f"Multiple PrepSessions found for Document {self.id}")
            return list(PrepSession.objects.filter(document=self.resource))[0]

    @property
    def georeference_sessions(self):
        return GeorefSession.objects.filter(document=self.id).order_by("date_run")

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
        if not self.parent_doc and self.preparation_session:
            cutlines = self.preparation_session.data['cutlines']
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

    @property
    def preparation_lock(self):

        lock = SessionLock()
        if self.preparation_session is not None:
            lock.set_from_session(self.preparation_session)
        return lock

    @property
    def georeference_lock(self):

        lock = SessionLock()
        for gs in self.georeference_sessions:
            if gs.stage != "finished":
                lock.set_from_session(gs)
        return lock

    @property
    def lock(self):
        return SessionLock(doc_proxy=self)

    def get_document(self):
        return Document.objects.get(id=self.id)

    def get_layer(self):

        try:
            link = GeoreferencedDocumentLink.objects.get(document=self.id)
            layer = Layer.objects.get(id=link.object_id)
        except (GeoreferencedDocumentLink.DoesNotExist, Layer.DoesNotExist, GeoreferencedDocumentLink.MultipleObjectsReturned):
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
            "layer_view": layer_urls.get("view", ""),
        }

    def get_split_summary(self):

        if self.preparation_session is None:
            return None

        info = self.preparation_session.serialize()

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

        sessions = [i.serialize() for i in self.georeference_sessions]
        return {
            "sessions": sessions,
            "gcp_geojson": self.gcps_geojson,
            "transformation": self.transformation,
        }

    def get_best_region_extent(self):
        """
        Gets the extent of the smallext region attached to this document.
        Could be improved to use the heirarchical region levels. Best would
        be an aggregation of all regions on the highest level (i.e. two
        adjacent towns).
        """
        # hard-code default Louisiana extent for now
        use_polygon = Polygon.from_bbox((-94, 28, -88, 33))
        for region in self.resource.regions.all().exclude(name="Global").exclude(name="Louisiana"):
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

        parent_doc = self.parent_doc
        if parent_doc is not None:
            parent_doc = parent_doc.serialize()

        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "urls": self.get_extended_urls(),
            "parent_doc": parent_doc,
            "lock": self.lock.as_dict,
        }

    def get_sessions(self):

        ps = self.preparation_session
        if ps is not None:
            gs = GeorefSession.objects.filter(document=self.resource).order_by("date_run")
            return list(chain([ps], gs))
        else:
            return []


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
            "view": full_reverse("new_map") + f"?layer={self.alternate}&view=True",
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

    @property
    def trim_sessions(self):
        return TrimSession.objects.filter(layer=self.id).order_by("date_run")

    @property
    def trim_lock(self):

        lock = SessionLock()
        for ts in self.trim_sessions:
            if ts.stage != "finished":
                lock.set_from_session(ts)
        return lock

    @property
    def lock(self):
        return SessionLock(layer_proxy=self)

    def get_layer(self):
        return Layer.objects.get(id=self.id)

    def get_layer_file(self):
        layer = self.get_layer()
        if layer is not None:
            lf = LayerFile.objects.filter(upload_session=layer.upload_session)
            if len(lf) == 1:
                return lf[0].file
        else:
            return None

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
        f = self.get_layer_file()
        urls['cog'] = ""
        if f is not None:
            site_base = settings.SITEURL.rstrip("/")
            urls['cog'] = site_base + f.url
        return urls

    def get_sessions(self):
        return TrimSession.objects.filter(layer=self.resource).order_by("date_run")
    
    def get_trim_summary(self):

        return {
            "sessions": [i.serialize() for i in self.trim_sessions],
            "vertex_ct": len(self.mask_coords),
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
            "lock": self.lock.as_dict,
            "mask_coords": self.mask_coords,
        }

def get_info_panel_content(resourceid):
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

    urls = {
        "refresh": full_reverse('georeference_info', args=(doc_proxy.id,)),
        "document_detail": doc_proxy.urls['detail'],
        "layer_detail": "",
        "split": doc_proxy.urls['split'],
        "georeference": doc_proxy.urls['georeference'],
        "trim": "",
    }
    sessions = doc_proxy.get_sessions()

    trim_summary = { "sessions": [] }
    layer_alternate = ""
    status = doc_proxy.status
    if layer_proxy is not None:
        status = layer_proxy.status
        layer_alternate = layer_proxy.alternate
        urls['layer_detail'] = layer_proxy.urls['detail']
        urls['trim'] = layer_proxy.urls['trim']
        trim_summary = layer_proxy.get_trim_summary()
        sessions = list(chain(sessions, layer_proxy.get_sessions()))

    serialized = [super(type(i), i).serialize() for i in sessions]
    serialized.sort(key=lambda i: (i['date_run'] is None, i['date_run']))

    context = {
        "STATUS": status,
        "RESOURCE_TYPE": resource_type,
        "DOCUMENT_ID": doc_proxy.id,
        "LAYER_ALTERNATE": layer_alternate,
        "URLS": urls,
        "SPLIT_SUMMARY": doc_proxy.get_split_summary(),
        "GEOREFERENCE_SUMMARY": doc_proxy.get_georeference_summary(),
        "TRIM_SUMMARY": trim_summary,
        "SESSION_HISTORY": serialized,
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
