import os
import json
import time
import uuid
import logging
import requests

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.layers.models import Layer

from georeference.utils import create_layer_from_vrt

from .models import Volume, Sheet
from .utils import LOCParser

logger = logging.getLogger(__name__)

class CollectionConnection(object):

    def __init__(self, verbose=False, delay=5):

        self.baseurl = "https://www.loc.gov"
        self.data = None
        self.results = []
        self.verbose = verbose
        self.query_url = ""
        self.delay = delay

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
        if self.verbose:
            print(f"query url: {url}")
        self.load_cache(url)
        if no_cache is False and self.data is None:
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


class Importer(object):

    def __init__(self, verbose=False, dry_run=False, delay=5):

        self.verbose = verbose
        self.dry_run = dry_run
        self.delay = delay
    
    def import_volumes(self, state=None, city=None, year=None, import_sheets=False):

        lc = CollectionConnection(
            delay=self.delay,
            verbose=self.verbose,
        )

        items = lc.get_items(
            locations=[i for i in [state, city] if not i is None],
            year=year,
        )

        if self.verbose:
            print(f"{len(items)} items retrieved")

        volumes = []
        for item in items:
            identifier = LOCParser().parse_item_identifier(item)
            location = LOCParser().parse_location_info(item)
            if location["state"] != state:
                continue

            if not self.dry_run:
                vol = Volume().create_from_lc_json(item)
                volumes.append(vol)

            if import_sheets is True and not self.dry_run:
                self.import_sheets(identifier)
        
        return volumes

    def import_volume(self, identifier, import_sheets=False):

        lc = CollectionConnection(
            delay=self.delay,
            verbose=self.verbose,
        )

        item = lc.get_item(
            identifier=identifier,
        )
        
        if item.get("status") == 404:
            return None

        vol = Volume().create_from_lc_json(item["item"])

        if import_sheets is True and not self.dry_run:
            self.import_sheets(identifier)

        return vol

    def import_sheets(self, volume_id):

        vol = Volume.objects.get(identifier=volume_id)
        if vol.lc_resources is None:
            lc = CollectionConnection(
                delay=self.delay,
                verbose=self.verbose,
            )
            data = lc.get_item(volume_id)
            vol.lc_resources = data['resources']
            vol.save()

        sheets = []
        for fileset in vol.lc_resources[0]['files']:
            info = LOCParser().parse_fileset(fileset)
            if self.dry_run:
                continue
            try:
                sheet = Sheet.objects.get(volume=vol, sheet_no=info["sheet_number"])
            except Sheet.DoesNotExist:
                sheet = Sheet().create_from_fileset(fileset, vol, fileset_info=info)
            sheets.append(sheet)
        
        return sheets
    
    def get_city_list_by_state(self, state):

        lc = CollectionConnection(
            delay=self.delay,
            verbose=self.verbose,
        )

        items = lc.get_items(locations=[state])

        cities = {}
        for item in items:
            identifier = LOCParser().parse_item_identifier(item)
            location = LOCParser().parse_location_info(item)
            if location["state"] != state:
                continue
            city = location["city"]
            cities[city] = cities.get(city, 0) + 1
        
        cities_list = [(k, v) for k, v in cities.items()]
        
        return sorted(cities_list)
    
    def get_volume_list_by_city(self, city, state):

        lc = CollectionConnection(
            delay=self.delay,
            verbose=self.verbose,
        )

        items = lc.get_items(
            locations=[i for i in [state, city] if not i is None],
        )

        if self.verbose:
            print(f"{len(items)} items retrieved")

        volumes = []
        for item in items:
            i = LOCParser().parse_item_identifier(item)
            l = LOCParser().parse_location_info(item)
            d = LOCParser().parse_date_info(item)
            n = LOCParser().parse_volume_number(item)
            s = LOCParser().parse_sheet_count(item)

            seg1 = str(d['year'])
            if n:
                seg1 += f" (vol. {n})"
            seg2 = f"{l['city']}, {l['county_equivalent']}"
            seg3 = f"{s} Sheet{'s' if s != 1 else ''}"

            title = " | ".join([seg2, seg1, seg3])

            d_facet = f"date__gte={d['year']}-01-01T00:00:00.000Z"
            r_facet = f"region__name__in={l['city']}"

            vol = {
                "identifier": i,
                "title": title,
                "year": d["year"],
                "url": reverse("volume_summary", args=(i,)),
                "started": Volume.objects.filter(identifier=i).exists(),
                "docs_search_url": f"{settings.SITEURL}documents/?{r_facet}&{d_facet}"
            }
            volumes.append(vol)

        return sorted(volumes, key=lambda k: k['title']) 


    def initialize_volume(self, volume):
        """Creates all of the necessary items to begin georeferencing a new volume.
        
        1) create two new Layer objects for the volume
            1) content layer is a VRT to which georeferenced sheets will be added.
            2) index layer is a VRT to which georeference index sheets will be added.
        2) create a new Map object from the new layers
            -- or, add the layers to an existing Map if one has already been made.
        3) import sheets for Volume, thereby creating Sheet <--> Document pairs.
        """

        ## create new Map
        
        admin_user = get_user_model().objects.get(username='admin')
        # layer_name = Layer.objects.all().first().alternate

        # map_id = m.id
        # print(map_id)
        vrt_path = "/home/adam/Octavian/LSU/thesis/repo/loc_insurancemaps/loc_insurancemaps/uploaded/documents/document/bHguVF4LTf-Ll_smPAmM8Q_modified.vrt"
        gs_info = create_layer_from_vrt(vrt_path)

        BBOX = [-180, 180, -90, 90]
        gn_layer = Layer.objects.create(
            name=gs_info['name'],
            workspace=gs_info['workspace_name'],
            store=gs_info['store'],
            storeType='dataStore',
            alternate='%s:%s' % (gs_info['workspace_name'], gs_info['name']),
            title="new layer title",
            owner=admin_user,
            uuid=str(uuid.uuid4()),
            bbox_x0=BBOX[0],
            bbox_x1=BBOX[1],
            bbox_y0=BBOX[2],
            bbox_y1=BBOX[3],
            data_quality_statement="this is the data quality statement",
        )

        print(gn_layer)
        m = Map()
        m.thumbnail_url = "https://tile.loc.gov/storage-services/service/gmd/gmd426m/g4264m/g4264cm/g097511883/09751_1883-0001.gif"
        m.create_from_layer_list(admin_user, [gn_layer], "title", "abstract")
        map_id = m.id
        print(map_id)
        
def create_map_from_layer_list(user, layers, title, abstract):

    m = Map()
    m.owner = user
    m.title = title
    m.abstract = abstract
    m.projection = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857')
    m.zoom = 0
    m.center_x = 0
    m.center_y = 0

    if m.uuid is None or m.uuid == '':
        m.uuid = str(uuid.uuid1())

    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(None)

    _layers = []
    for layer in layers:
        if not isinstance(layer, Layer):
            try:
                layer = Layer.objects.get(alternate=layer)
            except ObjectDoesNotExist:
                raise Exception(
                    f'Could not find layer with name {layer}')

        if not user.has_perm(
                'base.view_resourcebase',
                obj=layer.resourcebase_ptr):
            # invisible layer, skip inclusion or raise Exception?
            logger.error(
                'User %s tried to create a map with layer %s without having premissions' %
                (user, layer))
        else:
            _layers.append(layer)

    # Set bounding box based on all layers extents.
    # bbox format: [xmin, xmax, ymin, ymax]
    bbox = m.get_bbox_from_layers(_layers)
    m.set_bounds_from_bbox(bbox, m.projection)

    # Save the map in order to create an id in the database
    # used below for the maplayers.
    m.save()

    if _layers and len(_layers) > 0:
        index = 0
        for layer in _layers:
            MapLayer.objects.create(
                map=m,
                name=layer.alternate,
                ows_url=layer.get_ows_url(),
                stack_order=index,
                visibility=True
            )
            index += 1

    # Save again to persist the zoom and bbox changes and
    # to generate the thumbnail.
    m.set_missing_info()
    m.save(notify=True)

