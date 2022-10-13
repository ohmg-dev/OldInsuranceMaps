import os
import json
import time
import logging
import requests

from django.conf import settings

from loc_insurancemaps.models import Volume
from loc_insurancemaps.utils import LOCParser, filter_volumes_for_use, unsanitize_name

logger = logging.getLogger(__name__)

def import_all_available_volumes(state, apply_filter=True, verbose=False):
    """Preparatory step that runs through all cities in the provided
    state, filters the available volumes for those cities, and then
    imports each one to create a new Volume object."""

    lc = CollectionConnection(delay=0, verbose=verbose)
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
            Importer().import_volume(volume['identifier'])

class CollectionConnection(object):

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
            locations=[i for i in [state, city] if not i is None],
        )

        if self.verbose:
            print(f"{len(items)} items retrieved")

        volumes = []
        for item in items:
            parsed = LOCParser(item=item)
            
            serialized = parsed.serialize_to_volume()
            volumes.append(serialized)

        return sorted(volumes, key=lambda k: k['title'])

class Importer(object):

    def __init__(self, verbose=False, dry_run=False, delay=5):

        self.verbose = verbose
        self.dry_run = dry_run
        self.delay = delay

    def import_volume(self, identifier):

        lc = CollectionConnection(delay=0, verbose=True)
        response = lc.get_item(identifier)
        if response.get("status") == 404:
            return None

        parsed = LOCParser(item=response['item'], include_regions=True)
        volume_kwargs = parsed.volume_kwargs()

        # add resources to args, not in item (they exist adjacent)
        volume_kwargs["lc_resources"] = response['resources']

        volume = Volume.objects.create(**volume_kwargs)
        volume.regions.set(parsed.regions)

        return volume
