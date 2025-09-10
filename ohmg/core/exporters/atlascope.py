import json

from django.contrib.gis.geos import MultiPolygon, GEOSGeometry

from ..models import LayerSet


def generate_atlascope_properties(layerset: LayerSet):
    return {
        "identifier": layerset.map.identifier,
        "publisherShort": "Sanborn",
        "year": layerset.map.year,
        "bibliographicEntry": "_Richards standard atlas of the town of Greenfield_ (Richards Map Company, 1918)",
        "source": {"type": "tilejson", "url": layerset.tilejson_url},
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
