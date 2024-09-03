import json
import logging
from datetime import datetime
from typing import List, Optional, Any

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from ninja import (
    Field,
    Schema,
)

from avatar.templatetags.avatar_tags import avatar_url

from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import SessionLock, SessionBase

logger = logging.getLogger(__name__)


class UserSchema(Schema):
    username: str
    profile_url: str
    psesh_ct: int
    gsesh_ct: int
    total_ct: int = 0
    gcp_ct: int
    volumes: list
    load_ct: int
    image_url: str
    api_keys: List[str]

    @staticmethod
    def resolve_volumes(obj):
        """overrride the volumes property on the model in order to 
        create a super light-weight acquisition of volume info"""
        values = Volume.objects.filter(loaded_by=obj) \
            .order_by('city', 'year') \
            .values('identifier', 'city', 'year', 'volume_no')
        for i in values:
            i['url'] = reverse('map_summary', args=(i['identifier'], ))
            i['title'] = f"{i['city']} {i['year']}{' vol. ' + i['volume_no'] if i['volume_no'] else ''}"
        return values

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
    title: str = Field(..., alias="__str__")
    city: Optional[str]
    county_equivalent: Optional[str]
    state: Optional[str]
    year_vol: str
    sheet_ct: int
    stats: dict
    loaded_by: Optional[UserSchemaLite]
    load_date: str
    volume_no: Optional[str]
    urls: dict
    mj_exists: bool
    gt_exists: bool
    mosaic_preference: str

    @staticmethod
    def resolve_load_date(obj):
        load_date_str = ""
        if obj.load_date:
            load_date_str = obj.load_date.strftime("%Y-%m-%d")
        return load_date_str

    @staticmethod
    def resolve_year_vol(obj):
        year_vol = obj.year
        if obj.volume_no is not None:
            year_vol = f"{obj.year} vol. {obj.volume_no}"
        return str(year_vol)

    @staticmethod
    def resolve_urls(obj):
        return {
            "summary": reverse('map_summary', args=(obj.identifier, )),
            "viewer": reverse('map_summary', args=(obj.identifier, )),
        }


    @staticmethod
    def resolve_detail_url(obj):
        return reverse("resource_detail", args=(obj.pk, ))


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
            "resource": f"/resource/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            # "image": obj.file.url if obj.file else "",
            "split": f"/split/{obj.pk}",
        }


class RegionSchema(Schema):
    id: int
    title: str
    slug: str
    file: Optional[str]
    thumbnail: Optional[str]
    boundary: Optional[dict]
    georeferenced: bool
    urls: dict
    image_size: Optional[list]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/resource/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            # "image": obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.pk}",
        }

    @staticmethod
    def resolve_boundary(obj):
        if obj.boundary:
            return json.loads(obj.boundary.geojson)
        else:
            return None


class LayerSchema(Schema):
    id: int
    title: str
    slug: str
    detail_url: str
    thumb_url: Optional[str]
    geotiff_url: Optional[str]
    image_url: Optional[str]
    mask: Optional[dict]
    gcps_geojson: Optional[dict]
    urls: dict
    extent: Optional[list]

    @staticmethod
    def resolve_urls(obj):
        return {
            "resource": f"/resource/{obj.pk}",
            "thumbnail": obj.thumbnail.url if obj.thumbnail else "",
            "cog": settings.MEDIA_HOST.rstrip("/") + obj.file.url if obj.file else "",
            "georeference": f"/georeference/{obj.region.pk}",
        }

    @staticmethod
    def resolve_thumb_url(obj):
        if obj.thumbnail:
            return obj.thumbnail.url

    @staticmethod
    def resolve_detail_url(obj):
        return reverse("resource_detail", args=(obj.pk, ))

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
    def resolve_geotiff_url(obj):
        if obj.file:
            return obj.file.url
        else:
            return None

    @staticmethod
    def resolve_gcps_geojson(obj):
        if not obj.region:
            logger.warn(f"[WARNING] Layer {obj.pk} has no associated region")
            return None
        elif not obj.region.gcp_group:
            logger.warn(f"[WARNING] Region {obj.region.pk} has no associated GCPGroup")
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
    

class LayerAnnotationSchema(Schema):

    title: str
    slug: str
    urls: dict
    status: str
    extent: Optional[tuple]
    page_str: str = ""

    @staticmethod
    def resolve_urls(obj):
        return obj.urls

    @staticmethod
    def resolve_page_str(obj):
        return obj.title.split("|")[-1].split("p")[1]


class LayerSetSchema(Schema):

    id: str
    name: str
    volume_id: str
    is_geospatial: bool
    annotations: List[LayerAnnotationSchema]
    multimask_geojson: Optional[dict]
    extent: Optional[tuple]
    multimask_extent: Optional[tuple]
    mosaic_cog_url: Optional[str]
    mosaic_json_url: Optional[str]

    @staticmethod
    def resolve_id(obj):
        return str(obj.category.slug)

    @staticmethod
    def resolve_name(obj):
        return str(obj.category)

    @staticmethod
    def resolve_is_geospatial(obj):
        return obj.category.is_geospatial


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

class MapFullSchema(Schema):

    identifier: str
    title: str
    year: int = 0
    loaded_by: Optional[UserSchemaLite]
    status: str = ""
    access: str
    document_sources: list
    documents: List[DocumentSchema]
    # regions: List[RegionSchema]
    item_lookup: dict
    volume_number: Optional[str]
    document_page_type: str
    urls: dict
    progress: dict
    extent: Optional[Any]
    locale: Optional[PlaceSchema]
    loaded_by: dict
    # multimask: Optional[Any]
    # mosaic_preference: str = ""

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
        unprep_ct = len(obj.item_lookup['unprepared'])
        prep_ct = len(obj.item_lookup['prepared'])
        georef_ct = len(obj.item_lookup['georeferenced'])
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