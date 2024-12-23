from pathlib import Path

from ohmg.settings import *  # noqa: F403

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

ENABLE_DEBUG_TOOLBAR = True

# set all file handlers to use the test log directory
for handler in LOGGING["handlers"].values():  # noqa: F405
    if handler["class"] == "logging.FileHandler":
        newpath = LOG_DIR / Path(handler["filename"]).name
        handler["filename"] = str(newpath)
