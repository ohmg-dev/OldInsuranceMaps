from datetime import datetime
from typing import List, Optional, Any, Union
from django.conf import settings
from django.urls import reverse
from ninja import (
    Field,
    FilterSchema,
    Schema,
)

from avatar.templatetags.avatar_tags import avatar_url

from ohmg.loc_insurancemaps.models import Volume


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


class MapFullSchema(Schema):

    identifier: str
    title: str = Field(..., alias="__str__")
    year: int = 0
    loaded_by: Optional[UserSchemaLite]
    status: str = ""
    progress: dict
    extent: Optional[Any]
    multimask: Optional[Any]
    mosaic_preference: str = ""

    def resolve_extent(obj):
        return obj.extent.extent if obj.extent else None

    def resolve_progress(obj):
        items = obj.sort_lookups()
        unprep_ct = len(items['unprepared'])
        prep_ct = len(items['prepared'])
        georef_ct = len(items['georeferenced'])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        return {
            "unprep_ct": unprep_ct,
            "prep_ct": prep_ct,
            "georef_ct": georef_ct,
            "percent": percent,
        }


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


class DocumentSchema(Schema):
    id: int
    title: str
    detail_url: str
    thumb_url: str = ''

    @staticmethod
    def resolve_thumb_url(obj):
        if obj.thumbnail:
            return obj.thumbnail.url

    @staticmethod
    def resolve_detail_url(obj):
        return reverse("resource_detail", args=(obj.pk, ))


class LayerSchema(Schema):
    id: int
    title: str
    slug: str
    detail_url: str
    thumb_url: str = ''
    geotiff_url: Optional[str]
    image_url: Optional[str]
    mask: Optional[dict]
    gcps_geojson: Optional[dict]

    @staticmethod
    def resolve_thumb_url(obj):
        if obj.thumbnail:
            return obj.thumbnail.url

    @staticmethod
    def resolve_detail_url(obj):
        return reverse("resource_detail", args=(obj.pk, ))

    @staticmethod
    def resolve_mask(obj):
        if obj.vrs and obj.vrs.multimask and obj.slug in obj.vrs.multimask:
            return obj.vrs.multimask[obj.slug]
        else:
            return None

    @staticmethod
    def resolve_image_url(obj):
        base = settings.SITEURL.rstrip("/")
        doc = obj.get_document()
        if doc and doc.file:
            return base + doc.file.url
        else:
            return None

    @staticmethod
    def resolve_geotiff_url(obj):
        base = settings.SITEURL.rstrip("/")
        if obj.file:
            return base + obj.file.url
        else:
            return None

    @staticmethod
    def resolve_gcps_geojson(obj):
        doc = obj.get_document()
        if doc:
            return doc.gcps_geojson
        else:
            return None

class SessionSchema(Schema):

    id: int
    type: str
    user: UserSchemaLite
    note: Optional[str]
    # resource_id = int
    doc: DocumentSchema = None
    lyr: LayerSchema = None
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

class FilterSessionSchema(FilterSchema):
    username: Optional[str] = Field(q='user__username')
    item: Optional[List[int]] = Field(q=['doc_id', 'lyr_id'])
    resource: Optional[List[int]] = Field(q=['doc_id__in', 'lyr_id__in'])
    type: Optional[str]
    start_date: Optional[str] = Field(q='date_created__gte')
    end_date: Optional[str] = Field(q='date_created__lte')


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


class AnnotationSetSchema(Schema):

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

    name: str = Field(..., alias="__str__")
    maps: list
    url: str

    @staticmethod
    def resolve_maps(obj):
        values = Volume.objects.filter(locales__id__exact=obj.id) \
            .order_by('year') \
            .values('identifier', 'year', 'volume_no')
        for i in values:
            i['url'] = reverse('map_summary', args=(i['identifier'], ))
        return values

    @staticmethod
    def resolve_url(obj):
        return reverse('viewer', args=(obj.slug, ))
