from typing import Optional

from django.urls import reverse
from ninja import (
    Schema,
    Field
)


class UserSchema(Schema):
    username: str
    profile_url: str

    @staticmethod
    def resolve_profile_url(obj):
        return reverse('profile_detail', args=(obj.username, ))


class MapFullSchema(Schema):

    identifier: str
    title: str = Field(..., alias="__str__")
    year: int = None
    loaded_by: Optional[UserSchema]
    status: str = None
    progress: dict
    extent: tuple = None
    multimask: dict = None
    mosaic_preference: str = None

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
    city: str = None
    county_equivalent: str = None
    state: str = None
    year_vol: str
    sheet_ct: int
    stats: dict
    loaded_by: Optional[UserSchema]
    load_date: str
    volume_no: str = None
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
    def resolve_mj_exists(obj):
        return False if not obj.mosaic_json else True

    @staticmethod
    def resolve_gt_exists(obj):
        return False if not obj.mosaic_geotiff else True

    @staticmethod
    def resolve_urls(obj):
        return {
            "summary": reverse('map_summary', args=(obj.identifier, )),
            "viewer": reverse('map_summary', args=(obj.identifier, )),
        }

