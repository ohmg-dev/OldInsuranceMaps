import os
import json
import pytz
import time
import logging
import requests
from datetime import datetime

from django.conf import settings
from django.urls import reverse

from ohmg.core.utils import (
    full_capitalize,
)
from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import AnnotationSet, SetCategory

from ohmg.core.utils import (
    STATE_CHOICES,
)

logger = logging.getLogger(__name__)

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
        ## include the four New Orleans volumes that create the 
        ## first full mosaic of the city: v1-v2 1885, v3 1887, v4 1893
        elif v['city'] == "New Orleans":
            if v['year'] < 1894:
                v['include'] = True
        ## for all other cities, include volumes through 1910
        elif v['year'] < 1911:
            v['include'] = True

    return volumes

def load_city_name_misspellings(state_name):
    """ Currently unused as this is a small lookup and can live in this
    file for now. May be good to move it back out to a separate JSON file eventually. """

    # lookup = {}
    # file_path = os.path.join(settings.BASE_DIR, "loc_insurancemaps", "reference_data", "city-name-misspellings.json")
    # if not os.path.isfile(file_path):
    #     return lookup
    # with open(file_path, "r") as o:
    #     data = json.load(o)
    # lookup = data.get(state_name.lower(), {})

    lookup = {
        "louisiana": {
            "Jeannerette": "Jeanerette",
            "De Quincy": "DeQuincy",
            "De Ridder": "DeRidder",
            "Keatchie": "Keachi",
            "Saint Rose": "St. Rose",
            "Saint Martinville": "St. Martinville",
            "Saint Francisville": "St. Francisville"
        }
    }

    l = lookup.get(state_name, {})
    return l

def unsanitize_name(state, name):
    """must 'uncorrect' names from the interface which need to be passed to 
    the LC api. For example, in the LC database there is De Quincy, which
    should be DeQuincy. The input search term here may be DeQuincy, but it
    must be changed to De Quincy for the search to work properly."""

    lookup = load_city_name_misspellings(state)

    rev = {v: k for k, v in lookup.items()}

    return rev.get(name, name)

def import_all_available_volumes(state, apply_filter=True, verbose=False):
    """Preparatory step that runs through all cities in the provided
    state, filters the available volumes for those cities, and then
    imports each one to create a new Volume object."""

    lc = LOCConnection(delay=0, verbose=verbose)
    cities = lc.get_city_list_by_state(state)

    volumes = []
    for city in cities:
        lc.reset()
        city = unsanitize_name(state, city[0])
        vols = lc.get_volume_list_by_city(city, state)
        if apply_filter is True:
            vols = filter_volumes_for_use(vols)
            volumes += [i for i in vols if i['include'] is True]
        else:
            volumes += vols

    for volume in volumes:
        try:
            Volume.objects.get(pk=volume['identifier'])
        except Volume.DoesNotExist:
            import_volume(volume['identifier'])

def import_volume(identifier, locale=None, dry_run=False):

    try:
        volume = Volume.objects.get(pk=identifier)
        volume.locales.set([locale])
        volume.update_place_counts()

        # make sure a main-content layerset exists for this volume
        main_ls, _ = AnnotationSet.objects.get_or_create(
            category=SetCategory.objects.get(slug="main-content"),
            volume=volume,
        )
        return volume
    except Volume.DoesNotExist:
        pass

    lc = LOCConnection(delay=0, verbose=True)
    response = lc.get_item(identifier)
    if response.get("status") == 404:
        return None

    parsed = LOCParser(item=response['item'])
    volume_kwargs = parsed.volume_kwargs()

    # add resources to args, not in item (they exist adjacent)
    volume_kwargs["lc_resources"] = response['resources']

    if dry_run:
        return volume_kwargs
    else:
        volume = Volume.objects.create(**volume_kwargs)
        volume.locales.add(locale)
        volume.update_place_counts()
        # make sure a main-content layerset exists for this volume
        main_ls, _ = AnnotationSet.objects.get_or_create(
            category=SetCategory.objects.get(slug="main-content"),
            volume=volume,
        )
        return volume


class LOCParser(object):

    def __init__(self, item=None, fileset=None):

        # passing in an item will automatically parse it as a volume
        if item:
            self.item = item
            self.parse_item_identifier()
            self.parse_location_info()
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

    def parse_location_info(self):

        self.city = None
        self.county_equivalent = None
        self.state = None
        self.extra_location_tags = []

        # collect all location tags into a list.
        # handle the fact that sometimes each location tag is a dictionary like
        # {'bexar county': 'https://www.loc.gov/search/?at=item&fa=location:bexar+county&fo=json'}
        # while other times each location tag is just a string.
        location_tags = []
        for lyr in self.item['location']:
            if isinstance(lyr, dict):
                location_tags.append(list(lyr.keys())[0])
            else:
                location_tags.append(lyr)

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
        location_tags = [i for i in location_tags if i not in used_tags]
        city_seg = title_segs[0]
        misspellings = load_city_name_misspellings(self.state)
        if city_seg in misspellings:
            self.city = misspellings[city_seg]
        else:
            self.city = city_seg
        for lt in location_tags:
            if lt == city_seg.lower():
                used_tags.append(lt)

        location_tags = [i for i in location_tags if i not in used_tags]
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
        location_tags = [i for i in location_tags if i not in used_tags]
        if len(location_tags) > 0:
            msg = f"WARNING: unparsed location tags - {self.identifier} - {title} - {location_tags}"
            print(msg)

        self.extra_location_tags = location_tags

    def parse_date_info(self):
        """ Parse the date tag from LOC item. If any errors, or missing date tag, use Battle of Agincourt."""

        self.year = None
        self.month = None
        good_month = False
        self.datetime = None
        date_tag = self.item.get("date", None)
        if date_tag is None:
            logger.warning("no date tag on item")
            dt = datetime.strptime("1415-10-25", "%Y-%m-%d")
        else:
            try:
                dt = datetime.strptime(date_tag, "%Y-%m-%d")
                good_month = True
            except ValueError:
                try:
                    dt = datetime.strptime(date_tag, "%Y-%m")
                    good_month = True
                except ValueError:
                    try:
                        dt = datetime.strptime(date_tag, "%Y")
                    except ValueError:
                        logger.warning("problem parsing date: " + date_tag)
                        dt = datetime.strptime("1415-10-25", "%Y-%m-%d")

        d = pytz.utc.localize(dt)
        self.datetime = d
        self.year = d.year
        if good_month:
            self.month = d.month

    def parse_volume_number(self):

        volume_no = None
        created_published = self.item["item"].get("created_published", "")
        if isinstance(created_published, list):
            created_published = created_published[0]
        else:
            created_published = created_published.lower()

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
            "extra_location_tags": self.extra_location_tags,
            "sheet_ct": self.sheet_ct,
            "title": self.title,
            "status": status,
            "urls": {
                "summary": reverse("map_summary", args=(self.identifier,)),
            },
        }

    def volume_kwargs(self):

        data = self.serialize_to_volume()
        del data["status"]
        del data["urls"]
        del data["title"]
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

class LOCConnection(object):

    def __init__(self, verbose=False, delay=5):

        self.baseurl = "https://www.loc.gov"
        self.data = None
        self.results = []
        self.verbose = verbose
        self.query_url = ""
        self.delay = delay

    def reset(self):
        self.data = None
        self.results = []

    def make_cache_path(self, url=None):

        if url is None:
            url = self.query_url

        cache_dir = settings.CACHE_DIR
        if not os.path.isdir(cache_dir):
            os.mkdir(cache_dir)
        file_name = url.replace("/", "__") + ".json"
        cache_path = os.path.join(cache_dir, file_name)

        return cache_path

    def initialize_query(self, collection=None, identifier=None):

        if collection:
            self.query_url = f"{self.baseurl}/collections/{collection}"
            # set returned attributes
            self.query_url += "?at=search,results,pagination"
        elif identifier:
            self.query_url = f"{self.baseurl}/item/{identifier}"
            # set returned attributes
            self.query_url += "?at=item,resources"
        else:
            return

        # set format to json, count to 100
        self.query_url += "&fo=json&c=100"

    def add_location_param(self, locations=[]):

        fa_qry = "&fa=" + "|".join([f"location:{i}" for i in locations])
        self.query_url += fa_qry

    def add_date_param(self, date):

        date_qry = "&dates=" + date
        self.query_url += date_qry

    def load_cache(self, url):

        path = self.make_cache_path(url)
        if os.path.isfile(path):
            with open(path, "r") as op:
                self.data = json.loads(op.read())

    def save_cache(self, url):

        path = self.make_cache_path(url)
        with open(path, "w") as op:
            json.dump(self.data, op, indent=1)

    def perform_search(self, no_cache=False, page=1):

        # empty data property to start new search
        self.data = None

        url = self.query_url
        if page is not None:
            url += f"&sp={page}"
        self.load_cache(url)
        run_search = no_cache is True or self.data is None
        if self.verbose:
            print(f"query url: {url} | delay: {self.delay} | using cache: {not run_search}")
        if run_search:
            if self.verbose and self.delay > 0:
                print(f"waiting {self.delay} seconds before making a request...")
            time.sleep(self.delay)
            if self.verbose:
                print("making request")
            try:
                response = requests.get(url)
                if response.status_code in [500, 503]:
                    msg = f"{response.status_code} error, retrying in 5 seconds..."
                    logger.warn(msg)
                    if self.verbose:
                        print(msg)
                    time.sleep(5)
                    if self.verbose:
                        print("making request")
                    response = requests.get(url)
            except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError) as e:
                msg = f"API Error: {e}"
                print(msg)
                logger.warn(e)
                return
            
            self.data = json.loads(response.content)
            self.save_cache(url)
        else:
            if self.verbose:
                print("using cached query results")

        ## during location/year searches, multiple items are returned in a 'results' list
        if "results" in self.data:
            self.results += self.data["results"]

    def get_item(self, identifier, no_cache=False):

        ## during identifier queries, a single dict is returned and stored in self.data
        ## the dict has 'item' and 'resources' keys.
        self.initialize_query(identifier=identifier)
        self.perform_search(no_cache=no_cache)

        return self.data

    def get_items(self, locations=[], no_cache=False, year=None):

        self.initialize_query(collection="sanborn-maps")
        if len(locations) > 0:
            self.add_location_param(locations)
        if year is not None:
            self.add_date_param(year)

        page_no = 1
        while True:
            self.perform_search(no_cache=no_cache, page=page_no)
            if self.data['pagination']['next'] is not None:
                page_no += 1
            else:
                break

        return self.results

    def get_city_list_by_state(self, state):

        items = self.get_items(locations=[state])

        cities = {}
        for item in items:
            parsed = LOCParser(item=item)
            if parsed.state != state:
                continue
            city = parsed.city
            cities[city] = cities.get(city, 0) + 1
        cities_list = [(k, v) for k, v in cities.items()]

        return sorted(cities_list)

    def get_volume_list_by_city(self, city, state):

        items = self.get_items(
            locations=[i for i in [state, city] if i is not None],
        )

        if self.verbose:
            print(f"{len(items)} items retrieved")

        volumes = []
        for item in items:
            parsed = LOCParser(item=item)
            
            serialized = parsed.serialize_to_volume()
            volumes.append(serialized)

        return sorted(volumes, key=lambda k: k['title'])
