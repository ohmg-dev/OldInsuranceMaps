from .requests import CacheableRequest


def retrieve_srs_wkt(code):
    url = f"https://epsg.io/{code}.wkt"
    return CacheableRequest(url, cache_subdir="srs_wkt").get_content()
