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
    """Returns a dissolved geometry of all layer masks in this layerset.
    TODO: This should most likely be a method on LayerSet itself.
    """

    if layerset.multimask_geojson:
        collection = []
        for i in layerset.multimask_geojson["features"]:
            geom = GEOSGeometry(json.dumps(i["geometry"]))
            collection.append(geom)

        geoms = MultiPolygon(collection)
        return json.loads(geoms.unary_union.json)
    else:
        return {"type": "MultiPolygon", "coordinates": []}


def get_layerset_features(place: Place) -> list["AtlascopeLayersetFeature"]:
    """Returns a list of features for each layerset in this place that has an
    xyz tiles url. The features have catalog information for properties and a
    dissolved geometry of all layer masks."""

    maps = sorted(place.map_set.all().exclude(hidden=True), key=lambda x: x.year)

    features = []
    for map in maps:
        ls = map.get_layerset("main-content")
        if ls and ls.xyz_tiles_url:
            feature = AtlascopeLayersetFeature.from_orm(ls).dict()
            features.append(feature)

    return features


def generate_atlascope_extents(place: Place, override_data_name: str = None):
    """Returns a topojson representation of all layerset features for main content
    in this place."""

    features = get_layerset_features(place)
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


def generate_atlascope_dissolved_footprints(place: Place) -> dict:
    """Returns a dissolved polygon (or, often, a multipolygon) of all layer masks across
    all main content layersets attached to this place."""

    features = get_layerset_features(place)
    geom_list = []
    for i in features:
        geom_list.append(GEOSGeometry(json.dumps(i["geometry"])))
    combined = geom_list[0]
    for geom in geom_list[1:]:
        combined = combined.union(geom)
    return json.loads(combined.json)


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
