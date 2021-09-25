import uuid

from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.layers.utils import file_upload

from georeference.utils import create_layer_from_vrt

from ..models import Volume, Sheet
from ..api import APIConnection
from .parsers import (
    parse_fileset,
    parse_item_identifier,
    parse_location_info,
    parse_sheet_count,
    parse_volume_number,
    parse_date_info,
)


class Importer(object):

    def __init__(self, verbose=False, dry_run=False, delay=5):

        self.verbose = verbose
        self.dry_run = dry_run
        self.delay = delay
    
    def import_volumes(self, state=None, city=None, year=None, import_sheets=False):

        lc = APIConnection(
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
            identifier = parse_item_identifier(item)
            location = parse_location_info(item)
            if location["state"] != state:
                continue

            if not self.dry_run:
                vol = Volume().create_from_lc_json(item)
                volumes.append(vol)

            if import_sheets is True and not self.dry_run:
                self.import_sheets(identifier)
        
        return volumes

    def import_volume(self, identifier, import_sheets=False):

        lc = APIConnection(
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
            lc = APIConnection(
                delay=self.delay,
                verbose=self.verbose,
            )
            data = lc.get_item(volume_id)
            vol.lc_resources = data['resources']
            vol.save()

        sheets = []
        for fileset in vol.lc_resources[0]['files']:
            info = parse_fileset(fileset)
            if self.dry_run:
                continue
            try:
                sheet = Sheet.objects.get(volume=vol, sheet_no=info["sheet_number"])
            except Sheet.DoesNotExist:
                sheet = Sheet().create_from_fileset(fileset, vol, fileset_info=info)
            sheets.append(sheet)
        
        return sheets
    
    def get_city_list_by_state(self, state):

        lc = APIConnection(
            delay=self.delay,
            verbose=self.verbose,
        )

        items = lc.get_items(locations=[state])

        cities = {}
        for item in items:
            identifier = parse_item_identifier(item)
            location = parse_location_info(item)
            if location["state"] != state:
                continue
            city = location["city"]
            cities[city] = cities.get(city, 0) + 1
        
        cities_list = [(k, v) for k, v in cities.items()]
        
        return sorted(cities_list)
    
    def get_volume_list_by_city(self, city, state):

        lc = APIConnection(
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
            i = parse_item_identifier(item)
            l = parse_location_info(item)
            d = parse_date_info(item)
            n = parse_volume_number(item)
            s = parse_sheet_count(item)

            seg1 = str(d['year'])
            if n:
                seg1 += f" (vol. {n})"
            seg2 = f"{l['city']}, {l['county_equivalent']}"
            seg3 = f"{s} Sheet{'s' if s != 1 else ''}"

            title = " | ".join([seg2, seg1, seg3])

            vol = {
                "identifier": i,
                "title": title,
                "year": d["year"],
                "url": reverse("volume_summary", args=(i,)),
                "started": Volume.objects.filter(identifier=i).exists()
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
        vrt_path = "/home/adam/Octavian/LSU/thesis/repo/ohmg/ohmg/uploaded/documents/document/bHguVF4LTf-Ll_smPAmM8Q_modified.vrt"
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

