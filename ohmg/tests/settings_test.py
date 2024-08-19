from pathlib import Path

from ohmg.settings import *  # noqa: F403

TESTS_BASE_DIR = Path(__file__).parent / "root"
TESTS_BASE_DIR.mkdir(exist_ok=True)

LOG_DIR = TESTS_BASE_DIR / ".logs"
LOG_DIR.mkdir(exist_ok=True)

CACHE_DIR = TESTS_BASE_DIR / ".ohmg_cache"
CACHE_DIR.mkdir(exist_ok=True)

TEMP_DIR = TESTS_BASE_DIR / ".temp"
TEMP_DIR.mkdir(exist_ok=True)

STATIC_ROOT = TESTS_BASE_DIR / "static"
STATIC_ROOT.mkdir(exist_ok=True)

MEDIA_ROOT =TESTS_BASE_DIR / "uploaded"
MEDIA_ROOT.mkdir(exist_ok=True)

TEST_DATA_DIR = Path(__file__).parent / 'data'
