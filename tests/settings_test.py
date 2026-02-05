from pathlib import Path

from ohmg.conf.settings import *  # noqa: F403

# ref: https://www.inerciasensorial.com.br/2021/01/02/programacao/python/django-postgresql-used-session-on-github-actions-test-error/
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405

BASE_DIR = Path(__file__).parent / "root"
BASE_DIR.mkdir(exist_ok=True)

LOG_DIR = BASE_DIR / ".logs"
LOG_DIR.mkdir(exist_ok=True)

CACHE_DIR = BASE_DIR / ".ohmg_cache"
CACHE_DIR.mkdir(exist_ok=True)

TEMP_DIR = BASE_DIR / ".temp"
TEMP_DIR.mkdir(exist_ok=True)

STATIC_ROOT = BASE_DIR / "static"
STATIC_ROOT.mkdir(exist_ok=True)

MEDIA_ROOT = BASE_DIR / "uploaded"
MEDIA_ROOT.mkdir(exist_ok=True)

VRT_ROOT = Path(MEDIA_ROOT, "vrt")
VRT_ROOT.mkdir(exist_ok=True, parents=True)

## reset these S3 settings here to their default values, because they
## may be altered (during development) through the .env file.
MEDIA_URL = "/uploaded/"
ENABLE_S3_STORAGE = False
DEFAULT_FILE_STORAGE = "ohmg.core.storages.OverwriteStorage"

# set all file handlers to use the test log directory
for handler in LOGGING["handlers"].values():  # noqa: F405
    if handler["class"] == "logging.FileHandler":
        newpath = LOG_DIR / Path(handler["filename"]).name
        handler["filename"] = str(newpath)
