import os
import json
import pytz
from datetime import datetime

from django.conf import settings

from geonode.base.models import Region

from .enumerations import (
    STATE_CHOICES,
    MONTH_LOOKUP,
)

def load_city_name_misspellings(state_name):

    data = {}
    file_path = os.path.join(settings.LOCAL_ROOT, "reference_data", "city-name-misspellings.json")
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

    def parse_item_identifier(self, item):
        return item["id"].rstrip("/").split("/")[-1]

    def parse_sheet_count(self, item):
        sheet_ct = None
        if len(item["resources"]) > 0:
            sheet_ct = item["resources"][0]["files"]

        return sheet_ct

    def parse_location_info(self, item, include_regions=False):

        city, county_eq, state = None, None, None

        # collect all location tags into a list.
        # handle the fact that sometimes each location tag is a dictionary like
        # {'bexar county': 'https://www.loc.gov/search/?at=item&fa=location:bexar+county&fo=json'}
        # while other times each location tag is just a string.
        location_tags = []
        for l in item['location']:
            if isinstance(l, dict):
                location_tags.append(list(l.keys())[0])
            else:
                location_tags.append(l)

        # split the title of the item which has a lot of geographic info in it
        title = item["item"]["title"].replace("Sanborn Fire Insurance Map from ", "").rstrip(".")
        title_segs = [i.lstrip() for i in title.split(",")]

        used_tags = []

        # get state from the last item in the item title, easy
        state_names = [i[1] for i in STATE_CHOICES]
        state_seg = title_segs[-1]
        if state_seg in state_names:
            state = state_seg.lower()
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
        misspellings = load_city_name_misspellings(state)
        if city_seg in misspellings:
            city = misspellings[city_seg]
        else:
            city = city_seg
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
                        county_eq = full_capitalize(lt)
                        used_tags.append(lt)
        else:
            county_eq = county_seg
            for lt in location_tags:
                if lt in county_seg.lower():
                    used_tags.append(lt)

        # print leftover tags
        location_tags = [i for i in location_tags if not i in used_tags]
        if len(location_tags) > 0:
            msg = f"WARNING: unparsed location tags - {item['id']} - {title} - {location_tags}"
            print(msg)
        
        info = {
            "city": city,
            "county_equivalent": county_eq,
            "state": state,
            "extra": location_tags,
        }

        ## collect region objects. This should be combined to a single db call, but you 
        ## can't combine __iexact and __in, so not sure how to do this...
        if include_regions is True:
            regions = []
            regions += list(Region.objects.filter(name__iexact=city))
            regions += list(Region.objects.filter(name__iexact=county_eq))
            regions += list(Region.objects.filter(name__iexact=state))
            for tag in location_tags:
                regions += list(Region.objects.filter(name__iexact=tag))
            info["regions"] = regions

        return info

    def parse_date_info(self, item):

        info = {"year": None, "month": None}

        date_tag = item.get("date", None)
        if date_tag is None:
            return info

        try:
            dt = datetime.strptime(date_tag, "%Y-%m")
            d = pytz.utc.localize(dt)
            info["datetime"] = d
            info["year"] = d.year
            info["month"] = MONTH_LOOKUP[d.month]
        except ValueError:
            try:
                dt = datetime.strptime(date_tag, "%Y")
                d = pytz.utc.localize(dt)
                info["datetime"] = d
                info["year"] = d.year
            except ValueError:
                print("problem parsing date: " + date_tag)

        return info

    def parse_volume_number(self, item):

        volume_no = None
        created_published = item["item"].get("created_published", "").lower()
        if "vol." in created_published:
            a = created_published.split("vol.")[1]
            b = a.lstrip(" ").split(" ")
            volume_no = b[0].rstrip(",")
        
        return volume_no

    def parse_fileset(self, fileset):
        """this could be much improved to take better advantage of IIIF service
        returns."""

        info = {
            "jp2_url": None,
            "sheet_number": None,
            "iiif_service": None,
        }

        for f in fileset:
            if f['mimetype'] == "image/jp2":
                info["jp2_url"] = f['url']
                filename = f['url'].split("/")[-1]
                name = os.path.splitext(filename)[0]
                info["sheet_number"] = name.split("-")[-1].lstrip("0")
            if 'image-services' in f['url'] and '/full/' in f['url']:
                info["iiif_service"] = f['url'].split("/full/")[0]

        return info
