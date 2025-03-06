import os
import json
import time
import shutil
import string
import random
import requests
import logging
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.urls import reverse
from django.core.files import File

from PIL import Image

logger = logging.getLogger(__name__)


def make_cache_path(url):
    cache_dir = settings.CACHE_DIR / "requests"
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    file_name = url.replace("/", "__") + ".json"
    cache_path = os.path.join(cache_dir, file_name)

    return cache_path


def load_cache(url):
    path = make_cache_path(url)
    data = None
    if os.path.isfile(path):
        with open(path, "r") as op:
            data = json.loads(op.read())
    return data


def save_cache(url, data):
    path = make_cache_path(url)
    with open(path, "w") as op:
        json.dump(data, op, indent=1)


def make_cacheable_request(url, delay=0, no_cache=False):
    data = load_cache(url)
    run_search = no_cache is True or data is None

    if run_search:
        time.sleep(delay)
        try:
            response = requests.get(url)
            if response.status_code in [500, 503]:
                msg = f"{response.status_code} error, retrying in 5 seconds..."
                logger.warning(msg)
                time.sleep(5)
                response = requests.get(url)
        except (
            ConnectionError,
            ConnectionRefusedError,
            ConnectionAbortedError,
            ConnectionResetError,
        ) as e:
            msg = f"API Error: {e}"
            print(msg)
            logger.warning(e)
            return

        data = json.loads(response.content)
        save_cache(url, data)

    return data


def download_image(url: str, out_path: Path, retries: int = 3, use_cache: bool = True):
    if out_path.is_file() and use_cache:
        print(f"using cached file: {out_path}")
        return out_path

    # basic download code: https://stackoverflow.com/a/18043472/3873885
    while True:
        logger.debug(f"request {url}")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(out_path, "wb") as out_file:
                shutil.copyfileobj(response.raw, out_file)
            return out_path
        else:
            logger.warning(f"response code: {response.status_code} retries left: {retries}")
            time.sleep(5)
            retries -= 1
            if retries == 0:
                logger.warning("request failed, cancelling")
                return None


def copy_local_file_to_cache(path: str, out_path: Path, use_cache: bool = True):
    if not out_path.exists() or not use_cache:
        shutil.copyfile(path, out_path)


def save_file_to_object(target, file_path: Path = None, source_object=None):
    if file_path:
        source_path = file_path
    if source_object:
        if source_object.file:
            source_path = Path(source_object.file.path)
        else:
            print(f"[WARNING] {source_object} is missing file")

    with open(source_path, "rb") as openf:
        target.file.save(source_path.name, File(openf))


def convert_img_format(input_img: Path, format: str = "JPEG", force: bool = False) -> Path:
    ext_map = {"PNG": ".png", "JPEG": ".jpg", "TIFF": ".tif"}
    outpath = input_img.with_suffix(ext_map[format])

    if outpath.is_file() and not force:
        return outpath

    img = Image.open(input_img)
    img.save(outpath, format=format)

    return outpath


def full_capitalize(in_str):
    return " ".join([i.capitalize() for i in in_str.split(" ")])


def full_reverse(view_name, **kwargs):
    """Wraps the reverse utility to prepend the site base domain."""
    base = settings.SITEURL.rstrip("/")
    full_url = base + reverse(view_name, **kwargs)
    return full_url


def slugify(input_string, join_char="-"):
    output = input_string.lower()
    remove_chars = [".", ",", "'", '"', "|", "[", "]", "(", ")"]
    output = "".join([i for i in output if i not in remove_chars])
    for i in ["_", "  ", " - ", " ", "--", "-"]:
        output = output.replace(i, join_char)
    return output.lower()


def random_alnum(size=6):
    """
    Generate random 6 character alphanumeric string
    credit: https://codereview.stackexchange.com/a/232184
    """
    # List of characters [a-zA-Z0-9]
    chars = string.ascii_letters + string.digits
    code = "".join(random.choice(chars) for _ in range(size))
    return code


def time_this(func):
    def wrapper_function(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        logger.debug(
            f"{func.__module__} {func.__qualname__} elapsed time: {datetime.now() - start}"
        )
        return result

    return wrapper_function


def get_session_user_summary(session_list):
    users = session_list.values_list("user__username", flat=True)
    user_dict = {}
    for name in users:
        user_dict[name] = user_dict.get(
            name,
            {
                "ct": 0,
                "name": name,
            },
        )
        user_dict[name]["ct"] += 1
    return sorted(user_dict.values(), key=lambda item: item.get("ct"), reverse=True)


MONTH_CHOICES = [
    (1, "JAN."),
    (2, "FEB."),
    (3, "MAR."),
    (4, "APR."),
    (5, "MAY."),
    (6, "JUN."),
    (7, "JUL."),
    (8, "AUG."),
    (9, "SEP."),
    (10, "OCT."),
    (11, "NOV."),
    (12, "DEC."),
]
STATE_CHOICES = [
    ("alabama", "Alabama"),
    ("alaska", "Alaska"),
    ("arizona", "Arizona"),
    ("arkansas", "Arkansas"),
    ("california", "California"),
    ("colorado", "Colorado"),
    ("connecticut", "Connecticut"),
    ("delaware", "Delaware"),
    ("district of columbia", "District of Columbia"),
    ("florida", "Florida"),
    ("georgia", "Georgia"),
    ("hawaii", "Hawaii"),
    ("idaho", "Idaho"),
    ("illinois", "Illinois"),
    ("indiana", "Indiana"),
    ("iowa", "Iowa"),
    ("kansas", "Kansas"),
    ("kentucky", "Kentucky"),
    ("louisiana", "Louisiana"),
    ("maine", "Maine"),
    ("maryland", "Maryland"),
    ("massachusetts", "Massachusetts"),
    ("michigan", "Michigan"),
    ("minnesota", "Minnesota"),
    ("mississippi", "Mississippi"),
    ("missouri", "Missouri"),
    ("montana", "Montana"),
    ("nebraska", "Nebraska"),
    ("nevada", "Nevada"),
    ("new hampshire", "New Hampshire"),
    ("new jersey", "New Jersey"),
    ("new mexico", "New Mexico"),
    ("new york", "New York"),
    ("north carolina", "North Carolina"),
    ("north dakota", "North Dakota"),
    ("ohio", "Ohio"),
    ("oklahoma", "Oklahoma"),
    ("oregon", "Oregon"),
    ("pennsylvania", "Pennsylvania"),
    ("rhode island", "Rhode Island"),
    ("south carolina", "South Carolina"),
    ("south dakota", "South Dakota"),
    ("tennessee", "Tennessee"),
    ("texas", "Texas"),
    ("utah", "Utah"),
    ("vermont", "Vermont"),
    ("virginia", "Virginia"),
    ("washington", "Washington"),
    ("west virginia", "West Virginia"),
    ("wisconsin", "Wisconsin"),
    ("wyoming", "Wyoming"),
]
STATE_ABBREV = {
    "alabama": "Ala.",
    "alaska": "Alaska",
    "arizona": "Ariz.",
    "arkansas": "Ark.",
    "california": "Calif.",
    "colorado": "Colo.",
    "connecticut": "Conn.",
    "delaware": "Del.",
    "district of columbia": "D.C.",
    "florida": "Fla.",
    "georgia": "Ga.",
    "hawaii": "Hawaii",
    "idaho": "Idaho",
    "illinois": "Ill.",
    "indiana": "Ind.",
    "iowa": "Iowa",
    "kansas": "Kan.",
    "kentucky": "Ky.",
    "louisiana": "La.",
    "maine": "Maine",
    "maryland": "Md.",
    "massachusetts": "Mass.",
    "michigan": "Mich.",
    "minnesota": "Minn.",
    "mississippi": "Miss.",
    "missouri": "Mo.",
    "montana": "Mont.",
    "nebraska": "Neb.",
    "nevada": "Nev.",
    "new hampshire": "N.H.",
    "new jersey": "N.J.",
    "new mexico": "N.M.",
    "new york": "N.Y.",
    "north carolina": "N.C.",
    "north dakota": "N.D.",
    "ohio": "Ohio",
    "oklahoma": "Okla.",
    "oregon": "Ore.",
    "pennsylvania": "Pa.",
    "rhode island": "R.I.",
    "south carolina": "S.C.",
    "south dakota": "S.D.",
    "tennessee": "Tenn.",
    "texas": "Texas",
    "utah": "Utah",
    "vermont": "Vt.",
    "virginia": "Va.",
    "washington": "Wash.",
    "west virginia": "W.Va.",
    "wisconsin": "Wis.",
    "wyoming": "Wyo.",
}
STATE_POSTAL = {
    "alabama": "al",
    "alaska": "ak",
    "arizona": "az",
    "arkansas": "ar",
    "california": "ca",
    "colorado": "co",
    "connecticut": "cn",
    "delaware": "de",
    "district of columbia": "dc",
    "florida": "fl",
    "georgia": "ga",
    "hawaii": "hi",
    "idaho": "id",
    "illinois": "il",
    "indiana": "in",
    "iowa": "ia",
    "kansas": "ka",
    "kentucky": "ky",
    "louisiana": "la",
    "maine": "me",
    "maryland": "md",
    "massachusetts": "ma",
    "michigan": "mi",
    "minnesota": "mn",
    "mississippi": "ms",
    "missouri": "mo",
    "montana": "mt",
    "nebraska": "ne",
    "nevada": "nv",
    "new hampshire": "nh",
    "new jersey": "nj",
    "new mexico": "nm",
    "new york": "ny",
    "north carolina": "nc",
    "north dakota": "nd",
    "ohio": "oh",
    "oklahoma": "ok",
    "oregon": "or",
    "pennsylvania": "pa",
    "rhode island": "ri",
    "south carolina": "sc",
    "south dakota": "sd",
    "tennessee": "tn",
    "texas": "tx",
    "utah": "ut",
    "vermont": "vt",
    "virginia": "va",
    "washington": "wa",
    "west virginia": "wv",
    "wisconsin": "wi",
    "wyoming": "wy",
}
STATE_NAMES = [i[0] for i in STATE_CHOICES]
STATE_LOOKUP = {i[1]: i[0] for i in STATE_CHOICES}
STATE_POSTAL_LOOKUP = {v: k for k, v in STATE_POSTAL.items()}
