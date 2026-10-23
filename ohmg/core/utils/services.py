from urllib.parse import quote

from django.conf import settings


def encode_url(url: str):
    return quote(url, safe="")


def make_titiler_xyz_url(cog_url: str, tiles_2x: bool = False):
    format = "@2x.png" if tiles_2x else ".png"
    xyz_base = f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}{format}?"
    return f"{xyz_base}&url={encode_url(cog_url)}"


def make_titiler_wms_url(cog_url: str):
    return f"{settings.TITILER_HOST}/cog/wms/?LAYERS={encode_url(cog_url)}&VERSION=1.1.1"


def make_ohm_url(cog_url: str, lat: float, lon: float):
    xyz_url = make_titiler_xyz_url(cog_url, tiles_2x=True)
    return f"https://www.openhistoricalmap.org/edit#map=16/{lat}/{lon}&background=custom:{encode_url(xyz_url)}"


def make_tilejson(cog_url: str, lat: float, lon: float, extent: list[float, float, float, float]):
    return {
        "tilejson": "2.2.0",
        "version": "1.0.0",
        "scheme": "xyz",
        "tiles": [make_titiler_xyz_url(cog_url, tiles_2x=True)],
        "minzoom": 10,
        "maxzoom": 21,
        "bounds": extent,
        "center": [lon, lat, 16],
        "attribution": "<a href='https://oldinsurancemaps.net'>OldInsuranceMaps</a>; <a href='https://loc.gov/collections/sanborn-maps'>LOC</a>",
    }
