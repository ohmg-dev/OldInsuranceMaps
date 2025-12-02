import json

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from ninja import Schema

from ..core.models import LayerSet


def generate_atlascope_properties(layerset: LayerSet):
    return {
        "identifier": layerset.map.identifier,
        "publisherShort": "Sanborn",
        "year": layerset.map.year,
        "bibliographicEntry": "_Richards standard atlas of the town of Greenfield_ (Richards Map Company, 1918)",
        "source": {
            "type": "tilejson",
            "url": f"{settings.SITEURL.rstrip('/')}/map/{layerset.map.identifier}/{layerset.category.slug}/tilejson",
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
