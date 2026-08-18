import json

import topojson
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from ninja import Schema

from ..core.models import LayerSet
from ..places.models import Place


def generate_atlascope_properties(layerset: LayerSet):
    return {
        "identifier": layerset.map.identifier,
        "publisherShort": layerset.map.publisher
        if layerset.map.publisher
        else layerset.map.creator,
        "year": layerset.map.year,
        "bibliographicEntry": f"Fire Insurance Map of {layerset.map.title} (Sanborn Map Company)",
        "source": {
            "type": "xyz",
            "url": f"{layerset.xyz_tiles_url}/{{z}}/{{x}}/{{y}}.png",
        },
        "catalogPermalink": f"https://loc.gov/item/{layerset.map.identifier}",
        "heldBy": ["Library of Congress"],
        "sponsors": [],
    }


def generate_atlascope_geometry(layerset: LayerSet):
    if layerset.multimask_geojson:
        collection = []
        for i in layerset.multimask_geojson["features"]:
            geom = GEOSGeometry(json.dumps(i["geometry"]))
            collection.append(geom)

        geoms = MultiPolygon(collection)
        return json.loads(geoms.unary_union.json)
    else:
        return {"type": "MultiPolygon", "coordinates": []}


def generate_atlascope_footprints(place: Place, override_data_name: str = None):
    maps = sorted(place.map_set.all().exclude(hidden=True), key=lambda x: x.year)

    features = []
    for map in maps:
        ls = map.get_layerset("main-content")
        if ls and ls.xyz_tiles_url:
            feature = AtlascopeLayersetFeature.from_orm(ls).dict()
            features.append(feature)

    topo = topojson.Topology(
        {
            "type": "FeatureCollection",
            "features": features,
        }
    )
    topo_json = json.loads(topo.to_json())

    ## allow override of the data property name in the topojson
    if override_data_name:
        topo_json["objects"][override_data_name] = topo_json["objects"]["data"]
        del topo_json["objects"]["data"]

    return topo_json


class AtlascopeLayersetFeature(Schema):
    type: str = "Feature"
    properties: dict
    geometry: dict

    @staticmethod
    def resolve_properties(obj):
        return generate_atlascope_properties(obj)

    @staticmethod
    def resolve_geometry(obj):
        return generate_atlascope_geometry(obj)
