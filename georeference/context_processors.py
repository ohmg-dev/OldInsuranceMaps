from .proxy_models import get_georeference_info

def georeference_info(request):

    info = {}
    p = request.path

    # really messy parsing to get the layer alternate from the url
    if p.startswith("/layers/"):
        if not p.startswith("/layers/?") and p != "/layers/":
            spath = request.path.split("/")
            malt = spath[spath.index("layers") + 1]
            try:
                alt = ":".join([malt.split(":")[-2], malt.split(":")[-1]])
                info = get_georeference_info("layer", alt)
            except IndexError:
                pass

    # slightly cleaner parsing to get the document id from the url
    if request.path.startswith("/documents/"):
        spath = request.path.split("/")
        maybe_id = spath[spath.index("documents") + 1]
        if maybe_id.isdigit():
            info = get_georeference_info("document", maybe_id)

    return info