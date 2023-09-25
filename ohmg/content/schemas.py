from typing import List, Optional

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


class ItemFullSchema(Schema):

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


class ItemListSchema(Schema):
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
    volume_no: int = None
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
    def resolve_stats(obj):
        items = obj.sort_lookups()
        unprep_ct = len(items['unprepared'])
        prep_ct = len(items['prepared'])
        georef_ct = len(items['georeferenced'])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        main_lyrs_ct = 0
        if obj.sorted_layers:
            main_lyrs_ct = len(obj.sorted_layers['main'])
        mm_ct, mm_todo, mm_percent = 0, 0, 0
        if main_lyrs_ct != 0:
            # make sure 0/0 appears at the very bottom, then 0/1, 0/2, etc.
            mm_percent = main_lyrs_ct * .000001
        mm_display = f"0/{main_lyrs_ct}"
        if obj.multimask is not None:
            mm_ct = len(obj.multimask)
            mm_todo = main_lyrs_ct - mm_ct
            if mm_ct > 0:
                mm_display = f"{mm_ct}/{main_lyrs_ct}"
                mm_percent = mm_ct / main_lyrs_ct
                mm_percent += main_lyrs_ct * .000001

        return {
            "unprepared_ct": unprep_ct,
            "prepared_ct": prep_ct,
            "georeferenced_ct": georef_ct,
            "percent": percent,
            "mm_ct": mm_todo,
            "mm_display": mm_display,
            "mm_percent": mm_percent,
        }

    @staticmethod
    def resolve_mj_exists(obj):
        return False if not obj.mosaic_json else True

    @staticmethod
    def resolve_gt_exists(obj):
        return False if not obj.mosaic_geotiff else True

    @staticmethod
    def resolve_urls(obj):
        return {
            "summary": reverse('volume_summary', args=(obj.identifier, )),
            "viewer": reverse('volume_summary', args=(obj.identifier, )),
        }

