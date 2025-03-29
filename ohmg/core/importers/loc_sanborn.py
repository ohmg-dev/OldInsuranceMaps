import os
import json
import pytz
import time
import logging
import requests
from datetime import datetime

from django.conf import settings

from ohmg.core.utils import (
    full_capitalize,
    STATE_ABBREV,
)
from ohmg.core.importers.base import BaseImporter
from ohmg.places.models import Place
from ohmg.core.utils import (
    STATE_CHOICES,
)

logger = logging.getLogger(__name__)

## format for the city name misspelling lookup is
##   {
##       "state name": {
##           "wrong name": "right name",
##       }
##   }
LOC_SANBORN_CITY_MISSPELLINGS = {
    "louisiana": {
        "Jeannerette": "Jeanerette",
        "De Quincy": "DeQuincy",
        "De Ridder": "DeRidder",
        "Keatchie": "Keachi",
        "Saint Rose": "St. Rose",
        "Saint Martinville": "St. Martinville",
        "Saint Francisville": "St. Francisville",
    }
}


class LOCSanbornImporter(BaseImporter):
    """LOC Importer

    Load items from the Library of Congress Sanborn map collection.

    Required opts:

        identifier:   the LOC id for the item, looks like 'sanborn04339_026'
        locale:       slug for the locale to attach to the new map
    """

    required_input = [
        "identifier",
        "locale",
    ]

    def parse(self):
        identifier = self.input_data["identifier"]
        locale_slug = self.input_data["locale"]
        try:
            Place.objects.get(slug=locale_slug)
        except Place.DoesNotExist as e:
            raise e

        lc = LOCConnection(delay=0, verbose=True)

        no_cache = self.input_data.get("no-cache", "false")
        if no_cache.lower() == "true":
            no_cache = True
        response = lc.get_item(identifier, no_cache=no_cache)
        if response.get("status") == 404:
            raise ValueError("Can't get this resource from LC")

        parsed_item = LOCParser(item=response["item"])
        parsed_resources = LOCParser(resources=response["resources"])

        self.parsed_data = {
            "identifier": identifier,
            "title": parsed_item.title,
            "creator": "Sanborn Map Company",
            "year": parsed_item.year,
            "month": parsed_item.month,
            "locale": self.input_data["locale"],
            "document_sources": parsed_resources.document_sources,
            "volume_number": parsed_item.volume_no,
        }


class LOCParser(object):
    def __init__(self, item=None, resources=None):
        if item:
            self.item = item
            self.parse_item_identifier()
            self.parse_location_info()
            self.parse_volume_number()
            self.parse_sheet_count()
            self.parse_date_info()
            self.parse_manifest_url()
            self.parse_title()

        if resources:
            self.resources = resources
            self.parse_document_sources()

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
        for lyr in self.item["location"]:
            if isinstance(lyr, dict):
                location_tags.append(list(lyr.keys())[0])
            else:
                location_tags.append(lyr)

        # split the title of the item which has a lot of geographic info in it
        title = (
            self.item["item"]["title"].replace("Sanborn Fire Insurance Map from ", "").rstrip(".")
        )
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
            logger.warning(f"BAD STATE IN TITLE: {state_seg}")

        # get city
        location_tags = [i for i in location_tags if i not in used_tags]
        city_seg = title_segs[0]
        misspellings = LOC_SANBORN_CITY_MISSPELLINGS.get(self.state, {})
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
            logger.warning(
                f"unparsed location tags - {self.identifier} - {title} - {location_tags}"
            )

        self.extra_location_tags = location_tags

    def parse_date_info(self):
        """Parse the date tag from LOC item. If any errors, or missing date tag, use Battle of Agincourt."""

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

    def parse_title(self):
        title = f"{self.city}, {STATE_ABBREV[self.state]} | {self.year}"
        if self.volume_no is not None:
            title += f" | Vol. {self.volume_no}"

        self.title = title

    def get_page_number_from_url(self, url):
        filename = url.split("/")[-1]
        name = os.path.splitext(filename)[0]
        page_number = name.split("-")[-1].lstrip("0")
        if page_number == "":
            page_number = "0"

        return page_number

    def parse_document_sources(self):
        self.document_sources = []

        file_list = self.resources[0]["files"]

        for file_set in file_list:
            source = {
                "path": None,
                "iiif_info": None,
                "page_number": None,
            }
            for entry in file_set:
                if entry["mimetype"] == "image/jp2":
                    source["path"] = (url := entry.get("url"))
                    source["page_number"] = self.get_page_number_from_url(url)
                    source["iiif_info"] = entry.get("info")
            if source["path"]:
                self.document_sources.append(source)
            else:
                logger.error("No jp2 urls in this fileset, skipping")
                logger.debug(file_set)

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

        cache_dir = settings.CACHE_DIR / "requests"
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
            logger.info(f"query url: {url} | delay: {self.delay} | using cache: {not run_search}")
        if run_search:
            if self.verbose and self.delay > 0:
                logger.info(f"waiting {self.delay} seconds before making a request...")
            time.sleep(self.delay)
            logger.info("making request...")
            try:
                response = requests.get(url)
                if response.status_code in [500, 503]:
                    msg = f"{response.status_code} error, retrying in 5 seconds..."
                    logger.warning(msg)
                    if self.verbose:
                        print(msg)
                    time.sleep(5)
                    if self.verbose:
                        print("making request")
                    response = requests.get(url)
            except (
                ConnectionError,
                ConnectionRefusedError,
                ConnectionAbortedError,
                ConnectionResetError,
            ) as e:
                msg = f"API Error: {e}"
                print(msg)
                logger.warning(e)
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
