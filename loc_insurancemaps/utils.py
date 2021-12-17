import os
import json
import pytz
from datetime import datetime

from django.conf import settings
from django.urls import reverse

from geonode.base.models import Region

from .enumerations import (
    STATE_CHOICES,
)

def filter_volumes_for_use(volumes):
    """
    This is the primary filter function that is applied to a set of volumes
    from a given city (it must be a full list) and determines whether each
    one will be available in the current implementation.
    """

    ## set all to excluded first
    for volume in volumes:
        volume['include'] = False

    ## now iterate and selectively enable based on some criteria
    for n, v in enumerate(volumes):
        ## use the first volume for the city regardless of date
        if n == 0:
            v['include'] = True
        ## include the earliest New Orleans volumes
        elif v['city'] == "New Orleans":
            if v['year'] == 1885:
                v['include'] = True
        ## include all other volumes through 1910
        elif v['year'] < 1911:
            v['include'] = True

    return volumes

def load_city_name_misspellings(state_name):

    lookup = {}
    file_path = os.path.join(settings.LOCAL_ROOT, "reference_data", "city-name-misspellings.json")
    if not os.path.isfile(file_path):
        return lookup
    with open(file_path, "r") as o:
        data = json.load(o)
    lookup = data.get(state_name.lower(), {})
    return lookup

def unsanitize_name(state, name):
    """must 'uncorrect' names from the interface which need to be passed to 
    the LC api. For example, in the LC database there is De Quincy, which
    should be DeQuincy. The input search term here may be DeQuincy, but it
    must be changed to De Quincy for the search to work properly."""

    lookup = load_city_name_misspellings(state)

    rev = {v: k for k, v in lookup.items()}

    return rev.get(name, name)

def full_capitalize(in_str):
    return " ".join([i.capitalize() for i in in_str.split(" ")])

class LOCParser(object):

    def __init__(self, item=None, fileset=None, include_regions=False):

        # passing in an item will automatically parse it as a volume
        if item:
            self.item = item
            self.parse_item_identifier()
            self.parse_location_info(include_regions=include_regions)
            self.parse_volume_number()
            self.parse_sheet_count()
            self.parse_date_info()
            self.parse_manifest_url()
            self.create_item_title()

        # passing in a fileset will automatically parse it
        if fileset:
            self.fileset = fileset
            self.parse_fileset()

    def parse_item_identifier(self):
        self.identifier = self.item["id"].rstrip("/").split("/")[-1]

    def parse_sheet_count(self):
        self.sheet_ct = None
        if len(self.item["resources"]) > 0:
            sheet_ct = self.item["resources"][0]["files"]

        self.sheet_ct = sheet_ct

    def parse_location_info(self, include_regions=False):

        self.city = None
        self.county_equivalent = None
        self.state = None
        self.regions = []
        self.extra_location_tags = []

        # collect all location tags into a list.
        # handle the fact that sometimes each location tag is a dictionary like
        # {'bexar county': 'https://www.loc.gov/search/?at=item&fa=location:bexar+county&fo=json'}
        # while other times each location tag is just a string.
        location_tags = []
        for l in self.item['location']:
            if isinstance(l, dict):
                location_tags.append(list(l.keys())[0])
            else:
                location_tags.append(l)

        # split the title of the item which has a lot of geographic info in it
        title = self.item["item"]["title"].replace("Sanborn Fire Insurance Map from ", "").rstrip(".")
        title_segs = [i.lstrip() for i in title.split(",")]

        used_tags = []

        # get state from the last item in the item title, easy
        state_names = [i[1] for i in STATE_CHOICES]
        state_seg = title_segs[-1]
        if state_seg in state_names:
            self.state = state_seg.lower()
            # remove the location tag for the state
            for lt in location_tags:
                if lt == state_seg.lower():
                    used_tags.append(lt)
                    break
        else:
            print(f"BAD STATE IN TITLE: {state_seg}")
        
        # get city
        location_tags = [i for i in location_tags if not i in used_tags]
        city_seg = title_segs[0]
        misspellings = load_city_name_misspellings(self.state)
        if city_seg in misspellings:
            self.city = misspellings[city_seg]
        else:
            self.city = city_seg
        for lt in location_tags:
            if lt == city_seg.lower():
                used_tags.append(lt)

        location_tags = [i for i in location_tags if not i in used_tags]
        # find the county/parish and remove that from the tag list
        county_seg = None
        c_terms = ["county", "counties", "parish", "parishes", "census division"]
        for seg in title_segs:
            for t in c_terms:
                if t in seg.lower():
                    county_seg = seg

        if not county_seg:
            for lt in location_tags:
                for ct in c_terms:
                    if ct in lt.lower():
                        self.county_equivalent = full_capitalize(lt)
                        used_tags.append(lt)
        else:
            self.county_equivalent = county_seg
            for lt in location_tags:
                if lt in county_seg.lower():
                    used_tags.append(lt)

        # print leftover tags
        location_tags = [i for i in location_tags if not i in used_tags]
        if len(location_tags) > 0:
            msg = f"WARNING: unparsed location tags - {self.identifier} - {title} - {location_tags}"
            print(msg)

        self.extra_location_tags = location_tags

        ## collect region objects. This should be combined to a single db call, but you 
        ## can't combine __iexact and __in, so not sure how to do this...
        if include_regions is True:
            self.regions += list(Region.objects.filter(name__iexact=self.city))
            self.regions += list(Region.objects.filter(name__iexact=self.county_equivalent))
            self.regions += list(Region.objects.filter(name__iexact=self.state))
            for tag in location_tags:
                self.regions += list(Region.objects.filter(name__iexact=tag))

    def parse_date_info(self):

        self.year = None
        self.month = None
        self.datetime = None
        date_tag = self.item.get("date", None)
        if date_tag is None:
            return

        try:
            dt = datetime.strptime(date_tag, "%Y-%m")
            d = pytz.utc.localize(dt)
            self.datetime = d
            self.year = d.year
            self.month = d.month
        except ValueError:
            try:
                dt = datetime.strptime(date_tag, "%Y")
                d = pytz.utc.localize(dt)
                self.datetime = d
                self.year = d.year
            except ValueError:
                print("problem parsing date: " + date_tag)

    def parse_volume_number(self):

        volume_no = None
        created_published = self.item["item"].get("created_published", "").lower()
        if "vol." in created_published:
            a = created_published.split("vol.")[1]
            b = a.lstrip(" ").split(" ")
            volume_no = b[0].rstrip(",")

        self.volume_no = volume_no
    
    def parse_manifest_url(self):
        self.lc_manifest_url = f'{self.item["url"]}manifest.json'

    def create_item_title(self):

        seg1 = str(self.year)
        if self.volume_no:
            seg1 += f" (vol. {self.volume_no})"
        seg2 = f"{self.city}"
        seg3 = f"{self.sheet_ct} Sheet{'s' if self.sheet_ct != 1 else ''}"

        self.title = " | ".join([seg2, seg1, seg3])

    def serialize_to_volume(self):

        from .models import Volume

        try:
            v = Volume.objects.get(identifier=self.identifier)
            status = v.status
        except Volume.DoesNotExist:
            status = "not started"

        return {
            "identifier": self.identifier,
            "city": self.city,
            "county_equivalent": self.county_equivalent,
            "state": self.state,
            "year": self.year,
            "month": self.month,
            "volume_no": self.volume_no,
            "lc_item": self.item,
            "lc_manifest_url": self.lc_manifest_url,
            "regions": self.regions,
            "extra_location_tags": self.extra_location_tags,
            "sheet_ct": self.sheet_ct,
            "title": self.title,
            "status": status,
            "urls": {
                "summary": reverse("volume_summary", args=(self.identifier,)),
            },
        }

    def volume_kwargs(self):

        data = self.serialize_to_volume()
        del data["status"]
        del data["urls"]
        del data["title"]
        del data["regions"]
        return data

    def parse_fileset(self):
        """this could be much improved to take better advantage of IIIF service
        returns."""

        for f in self.fileset:
            if f['mimetype'] == "image/jp2":
                self.jp2_url = f['url']
                filename = f['url'].split("/")[-1]
                name = os.path.splitext(filename)[0]
                self.sheet_number = name.split("-")[-1].lstrip("0")
            if 'image-services' in f['url'] and '/full/' in f['url']:
                self.iiif_service = f['url'].split("/full/")[0]

    def serialize_to_fileset(self):

        return {
            "jp2_url": self.jp2_url,
            "sheet_number": self.sheet_number,
            "iiif_service": self.iiif_service,
        }




