import uuid
from typing import Union

import lxml.etree as et

from django.conf import settings

from ..models import Layer, LayerSet
from ..utils import retrieve_srs_wkt, get_file_url
from ..renderers import get_extent_from_file


def generate_qlr_content(instance: Union[Layer, LayerSet], titiler_host: str = settings.TITILER_HOST):
    title = str(instance)

    if isinstance(instance, Layer):
        file_url = get_file_url(instance)
        merc_extent = get_extent_from_file(instance.file, crs=3857)
        wgs84_extent = get_extent_from_file(instance.file, crs=4326)
    else:
        file_url = get_file_url(instance, "mosaic_geotiff")
        merc_extent = get_extent_from_file(instance.mosaic_geotiff, crs=3857)
        wgs84_extent = get_extent_from_file(instance.mosaic_geotiff, crs=4326)

    def make_element_with_text(tag: str, text: str, **kwargs):
        el = et.Element(tag, **kwargs)
        el.text = text
        return el

    id_str = f"_{str(uuid.uuid1()).replace('-', '_')}"

    layername_str = title
    datasource_str2 = (
        "crs=EPSG:3857&dpiMode=7&format=image/png&"
        + f"layers={file_url}&"
        + "tilePixelRatio=0&"
        + "styles&"
        + f"url={titiler_host}/cog/wms/?LAYERS%3D{file_url}%26VERSION%3D1.1.1"
    )

    wkt3857_str = retrieve_srs_wkt(3857)

    ## TODO: use a similar stategy here to the WKT retrieval: https://epsg.io/{code}.wkt
    proj43857_str = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs"

    qlr = et.Element("qlr")
    maplayers = et.SubElement(qlr, "maplayers")
    maplayer = et.SubElement(maplayers, "maplayer", type="raster")
    maplayer.append(make_element_with_text("id", id_str))
    maplayer.append(make_element_with_text("layername", layername_str))
    maplayer.append(make_element_with_text("datasource", datasource_str2))
    maplayer.append(make_element_with_text("provider", "wms"))

    extent = et.SubElement(maplayer, "extent")
    ymax, xmax, ymin, xmin = merc_extent
    extent.append(make_element_with_text("xmin", str(xmin)))
    extent.append(make_element_with_text("ymin", str(ymin)))
    extent.append(make_element_with_text("xmax", str(xmax)))
    extent.append(make_element_with_text("ymax", str(ymax)))

    extent = et.SubElement(maplayer, "wgs84extent")
    ymax84, xmax84, ymin84, xmin84 = wgs84_extent
    extent.append(make_element_with_text("xmin", str(xmin84)))
    extent.append(make_element_with_text("ymin", str(ymin84)))
    extent.append(make_element_with_text("xmax", str(xmax84)))
    extent.append(make_element_with_text("ymax", str(ymax84)))

    srs = et.SubElement(maplayer, "srs")
    spatailrefsys = et.SubElement(srs, "spatialrefsys", **{"nativeFormat": "Wkt"})
    spatailrefsys.append(make_element_with_text("wkt", wkt3857_str))
    spatailrefsys.append(make_element_with_text("proj4", proj43857_str))
    spatailrefsys.append(make_element_with_text("srsid", "3857"))
    spatailrefsys.append(make_element_with_text("srid", "3857"))
    spatailrefsys.append(make_element_with_text("authid", "EPSG:3857"))
    spatailrefsys.append(make_element_with_text("description", "WGS 84 / Pseudo-Mercator"))
    spatailrefsys.append(make_element_with_text("projectionacronym", "merc"))
    spatailrefsys.append(make_element_with_text("ellipsoidacronym", "EPSG:7030"))
    spatailrefsys.append(make_element_with_text("geographicflag", "false"))

    xml_str = et.tostring(
        qlr, pretty_print=True, doctype="<!DOCTYPE qgis-layer-definition>"
    ).decode()

    return xml_str
