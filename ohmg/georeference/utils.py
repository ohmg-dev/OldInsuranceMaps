import os
import string
import random
import logging

from django.conf import settings
from django.urls import reverse

from ohmg.georeference.georeferencer import get_path_variant

logger = logging.getLogger(__name__)

## ~~ general utils ~~

def full_reverse(view_name, **kwargs):
    """Wraps the reverse utility to prepend the site base domain."""
    base = settings.SITEURL.rstrip("/")
    full_url = base + reverse(view_name, **kwargs)
    return full_url

def slugify(input_string, join_char="-"):

    output = input_string.lower()
    remove_chars = [".", ",", "'", '"', "|", "[", "]", "(", ")"]
    output = "".join([i for i in output if not i in remove_chars])
    for i in ["_", "  ", " - ", " ", "--", "-"]:
        output = output.replace(i, join_char)
    return output.lower()

def analyze_url(request):

    p = request.path

    # really messy parsing to get the layer alternate from the url
    resource_type, res_id = None, None
    if p.startswith("/layers/"):
        resource_type = "layer"
        if not p.startswith("/layers/?") and p != "/layers/":
            spath = request.path.split("/")
            malt = spath[spath.index("layers") + 1]
            try:
                res_id = ":".join([malt.split(":")[-2], malt.split(":")[-1]])
            except IndexError:
                pass

    # slightly cleaner parsing to get the document id from the url
    if request.path.startswith("/documents/"):
        resource_type = "document"
        spath = request.path.split("/")
        maybe_id = spath[spath.index("documents") + 1]
        if maybe_id.isdigit():
            res_id = maybe_id

    return (resource_type, res_id)

def random_alnum(size=6):
    """
    Generate random 6 character alphanumeric string
    credit: https://codereview.stackexchange.com/a/232184
    """
    # List of characters [a-zA-Z0-9]
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(size))
    return code
