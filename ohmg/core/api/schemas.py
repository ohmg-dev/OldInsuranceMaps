import json
import logging
from datetime import datetime
from typing import List, Optional, Any, Literal

from natsort import natsorted

from django.conf import settings
from django.urls import reverse
from ninja import (
    Schema,
)

from avatar.templatetags.avatar_tags import avatar_url

from ohmg.core.models import (
    Document,
    Region,
    Layer,
)
from ohmg.georeference.models import (
    PrepSession,
    GeorefSession,
    SessionLock,
)

logger = logging.getLogger(__name__)


class MapListSchema(Schema):
    identifier: str
    title: str
    year: str


class UserSchema(Schema):
    username: str
    profile_url: str
    psesh_ct: int
    gsesh_ct: int
    total_ct: int = 0
    gcp_ct: int
    maps: List[MapListSchema]
    load_ct: int
    image_url: str

    @staticmethod
    def resolve_total_ct(obj):
        return obj.psesh_ct + obj.gsesh_ct

    @staticmethod
    def resolve_image_url(obj):
        return avatar_url(obj)


class UserSchemaLite(Schema):
    username: str
    profile_url: str


class MapListSchema(Schema):
    identifier: str
    title: str
    year_vol: str
    sheet_ct: int
    stats: dict
    loaded_by: Optional[UserSchemaLite]
    load_date: str
    volume_number: Optional[str]
    mj_exists: bool
    gt_exists: bool
    urls: dict

    @staticmethod
    def resolve_load_date(obj):
        load_date_str = ""
        if obj.load_date:
            load_date_str = obj.load_date.strftime("%Y-%m-%d")
        return load_date_str

    @staticmethod
    def resolve_year_vol(obj):
        year_vol = obj.year
        if obj.volume_number is not None:
            year_vol = f"{obj.year} vol. {obj.volume_number}"
        return str(year_vol)
    
    @staticmethod
    def resolve_sheet_ct(obj):
        return len(obj.document_sources)

    @staticmethod
    def resolve_urls(obj):
        return {
            "summary": f"/map/{obj.identifier}",
        }

class DocumentFullSchema(Schema):
    id: int
    title: str
    slug: str
    type: str = "document"
    status: str
    page_number: Optional[str]
    file: Optional[str]
    thumbnail: Optional[str]
    prepared: bool
    urls: dict
    image_size: Optional[list]
    lock: Optional["SessionLockSchema"]
    map: str
    cutlines: list
    regions: List["RegionSchema"]
    layers: List["LayerSchema"]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/document/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "image": obj.file.url if obj.file else "",
            "split": f"/split/{obj.pk}/",
        }

    @staticmethod
    def resolve_map(obj):
        return obj.map.pk
    
    @staticmethod
    def resolve_cutlines(obj):
        prep = PrepSession.objects.filter(doc2=obj)
        if prep.exists():
            return prep[0].data['cutlines']
        else:
            return []

    @staticmethod
    def resolve_status(obj):
        if obj.prepared:
            return "prepared"
        else:
            return "unprepared"


class DocumentSchema(Schema):
    id: int
    title: str
    slug: str
    page_number: Optional[str]
    file: Optional[str]
    thumbnail: Optional[str]
    prepared: bool
    urls: dict
    image_size: Optional[list]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/document/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "image": obj.file.url if obj.file else "",
            "split": f"/split/{obj.pk}/",
        }

class RegionSchema(Schema):
    id: int
    document_id: int
    title: str
    slug: str
    file: Optional[str]
    thumbnail: Optional[str]
    boundary: Optional[dict]
    georeferenced: bool
    urls: dict
    image_size: Optional[list]
    page_number: Optional[str]
    division_number: Optional[str]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/region/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "image": obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.pk}/",
        }

    @staticmethod
    def resolve_boundary(obj):
        if obj.boundary:
            return json.loads(obj.boundary.geojson)
        else:
            return None
        
    @staticmethod
    def resolve_page_number(obj):
        return obj.document.page_number


class RegionFullSchema(Schema):
    id: int
    title: str
    slug: str
    type: str = "region"
    status: str
    file: Optional[str]
    thumbnail: Optional[str]
    boundary: Optional[dict]
    georeferenced: bool
    urls: dict
    image_size: Optional[list]
    document: DocumentSchema
    layer: Optional["LayerSchema"]
    lock: Optional["SessionLockSchema"]
    map: str
    gcps_geojson: Optional[dict]
    transformation: Optional[str]
    page_number: Optional[str]
    division_number: Optional[str]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/region/{obj.pk}/",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "image": obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.pk}/",
        }

    @staticmethod
    def resolve_boundary(obj):
        if obj.boundary:
            return json.loads(obj.boundary.geojson)
        else:
            return None

    @staticmethod
    def resolve_layer(obj):
        if hasattr(obj, 'layer'):
            return obj.layer
        else:
            return None

    @staticmethod
    def resolve_map(obj):
        return obj.map.pk

    @staticmethod
    def resolve_status(obj):
        if obj.is_map is False:
            return "non-map"
        elif obj.georeferenced:
            return "georeferenced"
        else:
            return "prepared"

class LayerSchema(Schema):
    id: int
    title: str
    slug: str
    image_url: Optional[str]
    mask: Optional[dict]
    gcps_geojson: Optional[dict]
    urls: dict
    extent: Optional[list]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/layer/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "cog": settings.MEDIA_HOST.rstrip("/") + obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.region.pk}/",
        }

    @staticmethod
    def resolve_mask(obj):
        if obj.layerset and obj.layerset.multimask and obj.slug in obj.layerset.multimask:
            return obj.layerset.multimask[obj.slug]
        else:
            return None

    @staticmethod
    def resolve_image_url(obj):
        if obj.region and obj.region.file:
            return obj.region.file.url
        else:
            return None

    @staticmethod
    def resolve_gcps_geojson(obj):
        if not obj.region:
            logger.warning(f"[WARNING] Layer {obj.pk} has no associated region")
            return None
        elif not obj.region.gcp_group:
            logger.warning(f"[WARNING] Region {obj.region.pk} attached to Layer {obj.pk} has no associated GCPGroup")
            return None
        return obj.region.gcp_group.as_geojson
    

class LayerFullSchema(Schema):
    id: int
    title: str
    slug: str
    type: str = "layer"
    status: str = "georeferenced"
    image_url: Optional[str]
    mask: Optional[dict]
    gcps_geojson: Optional[dict]
    urls: dict
    extent: Optional[list]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/layer/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "cog": settings.MEDIA_HOST.rstrip("/") + obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.region.pk}/",
        }

    @staticmethod
    def resolve_mask(obj):
        if obj.layerset and obj.layerset.multimask and obj.slug in obj.layerset.multimask:
            return obj.layerset.multimask[obj.slug]
        else:
            return None

    @staticmethod
    def resolve_image_url(obj):
        if obj.region and obj.region.file:
            return obj.region.file.url
        else:
            return None

    @staticmethod
    def resolve_gcps_geojson(obj):
        if not obj.region:
            logger.warning(f"[WARNING] Layer {obj.pk} has no associated region")
            return None
        elif not obj.region.gcp_group:
            logger.warning(f"[WARNING] Region {obj.region.pk} attached to Layer {obj.pk} has no associated GCPGroup")
            return None
        return obj.region.gcp_group.as_geojson


class SessionSchema(Schema):

    id: int
    type: str
    user: UserSchemaLite
    note: Optional[str]
    doc2: Optional[DocumentSchema]
    reg2: Optional[RegionSchema]
    lyr2: Optional[LayerSchema]
    status: str
    stage: str
    data: dict
    user_input_duration: Optional[int]
    date_created: Optional[dict]

    @staticmethod
    def resolve_date_created(obj):
        d = {
            'date': obj.date_created.strftime("%Y-%m-%d"),
            'relative': ''
        }
        diff = datetime.now() - obj.date_created

        if diff.days > 0:
            n, u = diff.days, 'day'
        else:
            seconds = diff.total_seconds()
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            if hours > 0:
                n, u = hours, "hour"
            elif minutes > 0:
                n, u = minutes, "minute"
            else:
                n, u = seconds, "second"
        n = int(n)
        d['relative'] = f"{n} {u}{'' if n == 1 else 's'} ago"
        return d


class LayerSetLayer(Schema):

    id: int
    title: str
    local_title: str
    slug: str
    urls: dict
    extent: Optional[list]


    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/resource/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "cog": settings.MEDIA_HOST.rstrip("/") + obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.region.pk}/",
        }

    @staticmethod
    def resolve_local_title(obj):
        # TODO: this should probably be saved onto the model itself
        if obj.region:
            lt = obj.region.document.page_number
            if obj.region.division_number:
                lt = f"{lt} [{obj.region.division_number}]"
        else:
            lt = obj.title.split(" ")[-1]
        return lt


class LayerSetSchema(Schema):

    id: str
    name: str
    map_id: str
    layers: List[LayerSetLayer]
    multimask_geojson: Optional[dict]
    extent: Optional[tuple]
    multimask_extent: Optional[tuple]
    mosaic_cog_url: Optional[str]
    mosaic_json_url: Optional[str]

    @staticmethod
    def resolve_id(obj):
        return str(obj.category.slug)

    @staticmethod
    def resolve_layers(obj):
        return natsorted(obj.layers.all(), key=lambda k: k.title)

    @staticmethod
    def resolve_name(obj):
        return str(obj.category)


class PlaceSchema(Schema):
    """ very lightweight serialization of a Place with its Maps"""

    display_name: str
    slug: str
    maps: list
    url: str

    @staticmethod
    def resolve_maps(obj):
        return obj.map_set.all().order_by('year', 'title', 'volume_number').values("identifier", "title", "year", "volume_number")

    @staticmethod
    def resolve_url(obj):
        return reverse('viewer', args=(obj.slug, ))

class PlaceFullSchema(Schema):
    """ Full serialization of a Place to drive heirarchy search. """

    display_name: str
    slug: str
    maps: list
    url: str
    select_lists: dict
    breadcrumbs: list
    parents: List[PlaceSchema]
    descendants: List[PlaceSchema]
    volume_count: int
    volume_count_inclusive: int

    @staticmethod
    def resolve_maps(obj):
        return obj.map_set.all().order_by('year', 'title', 'volume_number').values("identifier", "title", "year", "volume_number")
    
    @staticmethod
    def resolve_select_lists(obj):
        return obj.get_select_lists()

    @staticmethod
    def resolve_breadcrumbs(obj):
        return obj.get_breadcrumbs()

    @staticmethod
    def resolve_url(obj):
        return reverse('viewer', args=(obj.slug, ))
    
    @staticmethod
    def resolve_parents(obj):
        return obj.direct_parents.all()

    @staticmethod
    def resolve_descendants(obj):
        return obj.get_descendants()


class SessionLockSchema(Schema):

    session_id: int
    target_id: int
    target_type: str
    user: UserSchemaLite

    @staticmethod
    def resolve_target_type(obj):
        return obj.target_type.model


class MapFullSchema(Schema):

    identifier: str
    title: str
    year: int = 0
    loaded_by: Optional[UserSchemaLite]
    status: str = ""
    access: str
    document_sources: list
    documents: List[DocumentSchema]
    item_lookup: dict
    volume_number: Optional[str]
    document_page_type: str
    urls: dict
    progress: dict
    extent: Optional[Any]
    locale: Optional[PlaceSchema]
    loaded_by: dict
    locks: List[SessionLockSchema]

    @staticmethod
    def resolve_extent(obj):
        return obj.extent
    
    @staticmethod
    def resolve_urls(obj):
        viewer_url = ""
        if obj.get_locale():
            viewer_url = f"/viewer/{obj.get_locale().slug}?{obj.identifier}=100"

        return {
            "summary": f"/map/{obj.identifier}",
            "viewer": viewer_url,
        }

    @staticmethod
    def resolve_progress(obj):

        unprep_ct = len(obj.item_lookup.get('unprepared', []))
        prep_ct = len(obj.item_lookup.get('prepared', []))
        georef_ct = len(obj.item_lookup.get('georeferenced', []))
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        return {
            "total_pages": len(obj.document_sources),
            "loaded_pages": obj.documents.exclude(file__in=["", None]).count(),
            "unprep_ct": unprep_ct,
            "prep_ct": prep_ct,
            "georef_ct": georef_ct,
            "percent": percent,
        }
    
    @staticmethod
    def resolve_locale(obj):
        return obj.get_locale()
    
    @staticmethod
    def resolve_loaded_by(obj):
        loaded_by = {"name": "", "profile": "", "date": ""}
        if obj.loaded_by is not None:
            loaded_by["name"] = obj.loaded_by.username
            loaded_by["profile"] = reverse("profile_detail", args=(obj.loaded_by.username, ))
            loaded_by["date"] = obj.load_date.strftime("%Y-%m-%d")
        return loaded_by
    
    @staticmethod
    def resolve_locks(obj):
        locks = [i for i in SessionLock.objects.all().prefetch_related() if i.target.map.pk == obj.pk]
        return locks
    
    @staticmethod
    def resolve_documents(obj):
        return natsorted(obj.documents.all(), key=lambda k: k.title)


class MapResourcesSchema(Schema):

    identifier: str
    title: str
    year: int = 0
    documents: List[DocumentSchema]
    regions: List[RegionSchema]
    volume_number: Optional[str]
    document_page_type: str
    urls: dict

    @staticmethod
    def resolve_urls(obj):
        viewer_url = ""
        if obj.get_locale():
            viewer_url = f"/viewer/{obj.get_locale().slug}?{obj.identifier}=100"

        return {
            "summary": f"/map/{obj.identifier}",
            "viewer": viewer_url,
        }

    @staticmethod
    def resolve_documents(obj):
        return natsorted(obj.documents.all(), key=lambda k: k.title)
    
    @staticmethod
    def resolve_regions(obj):
        return natsorted(obj.regions.all(), key=lambda k: k.title)


def _get_type_lookup(obj):
    return {
        Document: "document",
        Region: "region",
        Layer: "layer",
    }.get(obj.__class__)


class ResourceFullSchema(Schema):
    id: int
    title: str
    slug: str
    type: Literal['document', 'region', 'layer']
    status: str
    page_number: Optional[str]
    file: Optional[str]
    thumbnail: Optional[str]
    extent: Optional[list]
    urls: dict
    image_size: Optional[list]
    lock: Optional["SessionLockSchema"]
    map: str
    document: DocumentFullSchema
    region: Optional[RegionSchema]
    regions: List[RegionSchema]
    layers: List[LayerSchema]
    prep_sessions: List[SessionSchema]
    georef_sessions: List[SessionSchema]

    @staticmethod
    def resolve_type(obj):
        return _get_type_lookup(obj)

    @staticmethod
    def resolve_urls(obj):
        restype = _get_type_lookup(obj)
        docid, regid = None, None
        if restype == "layer":
            docid = obj.region.document.pk
            regid = obj.region.pk
        elif restype == "region":
            docid = obj.document.pk
            regid = obj.pk
        elif restype == "document":
            docid = obj.pk
        return {
            "resource": f"/{restype}/{obj.pk}",
            "split": f"/split/{docid}/",
            "georeference": f"/georeference/{regid}/",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "image": obj.file.url if obj.file else "",
            "cog": settings.MEDIA_HOST.rstrip("/") + obj.file.url if obj.file else "",
        }

    @staticmethod
    def resolve_map(obj):
        return obj.map.pk

    @staticmethod
    def resolve_document(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return obj.region.document
        elif restype == "region":
            return obj.document
        elif restype == "document":
            return obj

    @staticmethod
    def resolve_region(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return obj.region
        else:
            return None

    @staticmethod
    def resolve_regions(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return [obj.region]
        elif restype == "region":
            return obj.document.regions.all()
        elif restype == "document":
            return obj.regions.all()
    
    @staticmethod
    def resolve_layers(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return [obj]
        elif restype == "region":
            return [obj.layer] if hasattr(obj, 'layer') and obj.layer else []
        elif restype == "document":
            return obj.layers.all()
    
    @staticmethod
    def resolve_prep_sessions(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return PrepSession.objects.filter(doc2=obj.region.document)
        elif restype == "region":
            return PrepSession.objects.filter(doc2=obj.document)
        elif restype == "document":
            return PrepSession.objects.filter(doc2=obj)

    @staticmethod
    def resolve_georef_sessions(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return GeorefSession.objects.filter(lyr2=obj)
        elif restype == "region":
            return GeorefSession.objects.filter(reg2=obj)
        elif restype == "document":
            return GeorefSession.objects.filter(reg2__in=obj.regions.all())

    @staticmethod
    def resolve_status(obj):
        restype = _get_type_lookup(obj)
        if restype == "layer":
            return "georeferenced"
        elif restype == "region":
            return "georeferenced" if obj.georeferenced else "prepared"
        elif restype == "document":
            reg_count = obj.regions.all().count()
            if reg_count == 0:
                return "unprepared"
            elif reg_count == 1:
                return "georeferenced" if obj.regions.all()[0].georeferenced else "prepared"
            else:
                return "split"


DocumentFullSchema.update_forward_refs()
RegionFullSchema.update_forward_refs()
