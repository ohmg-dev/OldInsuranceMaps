import os
import json
import time
import requests
from datetime import datetime
from django.conf import settings

from lc_insurancemaps.models import MapCollectionItem, MapScan
from lc_insurancemaps.views import get_volume_sheets

from .utils.enumerations import STATE_CHOICES


class APIConnection(object):

    def __init__(self, verbose=False):

        self.baseurl = "https://www.loc.gov"
        self.data = None
        self.results = []
        self.verbose = verbose

    def make_cache_path(self, url=None):

        if url is None:
            url = self.query_url

        cache_dir = settings.CACHE_DIR
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
            self.query_url = ""
            return

        # set format to json, count to 50
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
        if self.verbose:
            print(f"query url: {url}")
        self.load_cache(url)
        if no_cache is False and self.data is None:
            if self.verbose:
                print("waiting 5 seconds before making a request...")
            time.sleep(5)
            if self.verbose:
                print("making request")
            response = requests.get(url)
            if response.status_code in [500, 503]:
                if self.verbose:
                    print(f"{response.status_code} error, retrying in 5 seconds...")
                time.sleep(5)
                if self.verbose:
                    print("making request")
                response = requests.get(url)
            self.data = json.loads(response.content)
            self.save_cache(url)
        else:
            if self.verbose:
                print("using cached query results")

        for item in self.data['results']:
            if "item" in item:
                self.results.append(item)

        return

    def get_item(self, identifier, no_cache=False):

        self.initialize_query(identifier=identifier)
        self.perform_search(searchurl, no_cache=no_cache)

    def get_items(self, locations=[], no_cache=False, get_sheets=False, date=None, dry_run=False):

        self.initialize_query(collection="sanborn-maps")
        if len(locations) > 0:
            self.add_location_param(locations)
        if date is not None:
            self.add_date_param(date)

        page_no = 1
        while True:
            self.perform_search(no_cache=no_cache, page=page_no)
            if self.data['pagination']['next'] is not None:
                page_no += 1
            else:
                break

    def import_items(self, locations=[], no_cache=False, get_sheets=False, date="", dry_run=False):

        result_ct = self.data['search']['hits']

        if self.verbose:
            print(f"results: {result_ct}")
        if result_ct == 0:
            return

        # results = data.pop('results')
        for result in data['results']:

            result_year = result['date'].split("-")[0]
            if date != "" and result_year != date:
                if self.verbose:
                    print(f"skipping date: {result['date']}")
                continue

            if dry_run is False:
                item = MapCollectionItem().create_from_json(result)
            if get_sheets:
                if self.verbose:
                    print("getting sheets for:")
                    print(item)
                if dry_run is False:
                    self.get_sheets(item, no_cache=no_cache)


    def get_item_by_identifier(self, identifier, no_cache=False, get_sheets=False):

        data = self.get_item_json(identifier, no_cache=no_cache)

        item = MapCollectionItem().create_from_json(data['item'])
        item.loc_json = data
        item.save()
        item.save()
        if get_sheets:
            self.get_sheets(item, no_cache=no_cache)

        return item

    def get_sheets(self, volume, no_cache=False, dry_run=False):

        # If this volume was added as part of set of search results, then the
        # loc_json field will be empty, because that level of detail is not
        # acquired through basic search results. Thus, the extra call here.
        if volume.loc_json is None:
            data = self.get_item_json(volume.doi, no_cache=no_cache)
            volume.loc_json = data
            volume.save()

        volume.get_all_sheets()
