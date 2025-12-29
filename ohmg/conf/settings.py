import ast
import os
from pathlib import Path

from kombu import Exchange, Queue

MODE = os.getenv("MODE", "DEV")

# set the repo root as the BASE_DIR, project root at PROJECT_DIR
# Build paths inside the project like this: BASE_DIR / 'subdir'.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# set BASE_DIR which is used to locate log, cache, temp, static, and uploaded dirs
BASE_DIR = PROJECT_DIR.parent

# the build file is generated and updated with python manage.py update_build
BUILD_FILE = BASE_DIR / ".build"
BUILD_NUMBER = ""
if BUILD_FILE.is_file():
    with open(BUILD_FILE, "r") as o:
        BUILD_NUMBER = o.read()

SECRET_KEY = os.getenv("SECRET_KEY")
WSGI_APPLICATION = "ohmg.conf.wsgi.application"

# Location of url mappings
ROOT_URLCONF = "ohmg.conf.urls"

DEBUG = ast.literal_eval(os.getenv("DEBUG", "False"))

# add trailing slash to site url. geoserver url will be relative to this
SITEURL = os.getenv("SITEURL", "http://localhost:8000/")
if not SITEURL.endswith("/"):
    SITEURL += "/"

SITE_ID = int(os.getenv("SITE_ID", "1"))
SITE_NAME = os.getenv("SITENAME", "Example.com")

OHMG_API_KEY_FILEPATH = os.getenv("OHMG_API_KEY_FILEPATH", Path(BASE_DIR, ".ohmg_api_key"))
if Path(OHMG_API_KEY_FILEPATH).is_file():
    with open(OHMG_API_KEY_FILEPATH, "r") as o:
        OHMG_API_KEY = o.read().rstrip()
else:
    OHMG_API_KEY = os.getenv("OHMG_API_KEY")
if not OHMG_API_KEY:
    print("No API key configured. Consult documentation for guidance.")

ALLOWED_HOSTS = ast.literal_eval(os.getenv("ALLOWED_HOSTS", "[]"))

# Set path to cache directory
LOG_DIR = os.getenv("LOG_DIR", BASE_DIR / ".logs")
CACHE_DIR = os.getenv("CACHE_DIR", BASE_DIR / ".ohmg_cache")
TEMP_DIR = os.getenv("TEMP_DIR", BASE_DIR / ".temp")

for d in [LOG_DIR, CACHE_DIR, TEMP_DIR]:
    if not os.path.isdir(d):
        os.mkdir(d)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en")

INSTALLED_APPS = [
    "grappelli",
    "ohmg.accounts",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.redirects",
    "django.contrib.admin",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.gis",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "pinax.announcements",
    "storages",
    "django_extensions",
    "django_json_widget",
    "avatar",
    "compressor",
    "ninja",
    "markdownx",
    "ohmg.api",
    "ohmg.conf",
    "ohmg.core",
    "ohmg.extensions",
    "ohmg.frontend",
    "ohmg.georeference",
    "ohmg.places",
]

GRAPPELLI_ADMIN_TITLE = "OHMG"

MARKDOWNX_IMAGE_MAX_SIZE = {"size": (800, 0), "quality": 90}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.SHA1PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptPasswordHasher',
]

TEMPLATES = [
    {
        "NAME": "Project Templates",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            PROJECT_DIR / "frontend" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ohmg.frontend.context_processors.site_info",
            ],
            "debug": DEBUG,
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "ohmg"),
        "USER": os.getenv("DATABASE_USER", "postgres"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "postgres"),
        "HOST": os.getenv("DATABASE_HOST", "localhost"),
        "PORT": os.getenv("DATABASE_PORT", 5432),
    }
}


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
DEFAULT_FILE_STORAGE = "ohmg.core.storages.OverwriteStorage"

STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", BASE_DIR / "static_root")
# explicitly add the non-standard location of svelte build files
STATICFILES_DIRS = [
    PROJECT_DIR / "frontend" / "svelte_components" / "public" / "build",
]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

PLUGIN_ASSETS = (
    "https://code.jquery.com/jquery-2.2.4.min.js",
    "https://cdn.jsdelivr.net/npm/eldarion-ajax@0.16.0/js/eldarion-ajax.min.js",
    "https://cdn.jsdelivr.net/npm/bulma@1.0.0/css/bulma.min.css",
    "https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/style.css",
    "https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/Phosphor-Bold.svg",
    "https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/Phosphor-Bold.ttf",
    "https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/Phosphor-Bold.woff",
    "https://unpkg.com/@phosphor-icons/web@2.1.1/src/bold/Phosphor-Bold.woff2",
    "https://cdn.jsdelivr.net/npm/ol@v10.0.0/ol.css",
)

COMPRESS_ENABLED = True

MEDIA_URL = os.getenv("MEDIA_URL", "/uploaded/")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", BASE_DIR / "uploaded")

# create pattern for holding and serving temp VRT files
VRT_URL = "/uploaded/vrt/"
VRT_ROOT = Path(MEDIA_ROOT, "vrt")
VRT_ROOT.mkdir(exist_ok=True, parents=True)

# this is a custom setting to allow apache to be used in development
LOCAL_MEDIA_HOST = os.getenv("LOCAL_MEDIA_HOST", SITEURL)

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

EMAIL_ENABLE = ast.literal_eval(os.getenv("EMAIL_ENABLE", "False"))
if EMAIL_ENABLE:
    EMAIL_BACKEND = os.getenv(
        "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
    )
    EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "localhost")
    EMAIL_PORT = os.getenv("DJANGO_EMAIL_PORT", 25)
    EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = ast.literal_eval(os.getenv("DJANGO_EMAIL_USE_TLS", "False"))
    EMAIL_USE_SSL = ast.literal_eval(os.getenv("DJANGO_EMAIL_USE_SSL", "False"))
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Hello <hello@oldinsurancemaps.net>")
else:
    EMAIL_BACKEND = os.getenv(
        "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
    )

ENABLE_NEWSLETTER = ast.literal_eval(os.getenv("ENABLE_NEWSLETTER", "False"))
if ENABLE_NEWSLETTER:
    INSTALLED_APPS += (
        "sorl.thumbnail",
        "newsletter",
    )
    NEWSLETTER_THUMBNAIL = "sorl-thumbnail"
    NEWSLETTER_CONFIRM_EMAIL_SUBSCRIBE = True
    NEWSLETTER_CONFIRM_EMAIL_UNSUBSCRIBE = False
    NEWSLETTER_CONFIRM_EMAIL_UPDATE = False
    NEWSLETTER_RICHTEXT_WIDGET = "markdownx.widgets.AdminMarkdownxWidget"

# gravatar settings
AUTO_GENERATE_AVATAR_SIZES = (20, 30, 32, 40, 50, 65, 70, 80, 100, 140, 200, 240)
AVATAR_GRAVATAR_SSL = ast.literal_eval(os.getenv("AVATAR_GRAVATAR_SSL", "False"))

AVATAR_DEFAULT_URL = os.getenv("AVATAR_DEFAULT_URL", "icons/noun-user-1213267-FFFFFF.png")

PLAUSIBLE_DATA_DOMAIN = os.getenv("PLAUSIBLE_DATA_DOMAIN")
PLAUSIBLE_SOURCE_SCRIPT = os.getenv("PLAUSIBLE_SOURCE_SCRIPT")

PROSOPO_SITE_KEY = os.getenv("PROSOPO_SITE_KEY")
PROSOPO_SECRET_KEY = os.getenv("PROSOPO_SECRET_KEY")

try:
    # try to parse python notation, default in dockerized env
    AVATAR_PROVIDERS = ast.literal_eval(os.getenv("AVATAR_PROVIDERS"))
except ValueError:
    # fallback to regular list of values separated with misc chars
    AVATAR_PROVIDERS = (
        (
            "avatar.providers.PrimaryAvatarProvider",
            "avatar.providers.DefaultAvatarProvider",
        )
        if os.getenv("AVATAR_PROVIDERS") is None
        else os.getenv("AVATAR_PROVIDERS").split(",")
    )

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@localhost")

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
    "ohmg.conf.middleware.CORSMiddleware",
)

CORS_WHITELIST = (
    "/iiif/*",
    "/atlascope/*",
    "*/tilejson",
)

LOGIN_URL = "/account/login/"

LOGIN_REQUIRED_SITEWIDE = ast.literal_eval(os.getenv("LOGIN_REQUIRED_SITEWIDE", "False"))
if LOGIN_REQUIRED_SITEWIDE:
    MIDDLEWARE += ("ohmg.conf.middleware.LoginRequiredMiddleware",)

ENABLE_CPROFILER = ast.literal_eval(os.getenv("ENABLE_CPROFILER", "False"))
if ENABLE_CPROFILER:
    MIDDLEWARE += ("django_cprofile_middleware.middleware.ProfilerMiddleware",)

ENABLE_DEBUG_TOOLBAR = ast.literal_eval(os.getenv("ENABLE_DEBUG_TOOLBAR", "False"))
if DEBUG and ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE = ("debug_toolbar.middleware.DebugToolbarMiddleware",) + MIDDLEWARE
    INTERNAL_IPS = ["127.0.0.1"]

TITILER_HOST = os.getenv("TITILER_HOST", "")

OPENLAYERS_MAX_TILES_LOADING = os.getenv("OPENLAYERS_MAX_TILES_LOADING", 32)

## These creds are only actually used by boto3 if ENABLE_S3_STORAGE = True,
## or by the initialze-s3-bucket command as default values
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")

AWS_QUERYSTRING_AUTH = False
AWS_S3_VERIFY = True
AWS_S3_FILE_OVERWRITE = True
AWS_LOCATION = "uploaded/"

ENABLE_S3_STORAGE = ast.literal_eval(os.getenv("ENABLE_S3_STORAGE", "False"))

if ENABLE_S3_STORAGE:
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/uploaded/"
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# this is a hack to handle the fact that certain GDAL and Django versions
# are not compatible, and the order of lat/long gets messed up. ONLY to
# be used in development!!!!
# this will be removed once Django is upgraded
SWAP_COORDINATE_ORDER = ast.literal_eval(os.getenv("SWAP_COORDINATE_ORDER", "False"))

# CONFIGURE CELERY
CELERY_BROKER_URL = os.getenv("BROKER_URL")
CELERY_RESULT_BACKEND = "rpc://"

# basic independent setup for Celery Exchange/Queue
DEFAULT_EXCHANGE = Exchange("default", type="topic")
# CELERY_TASK_QUEUES += (
CELERY_TASK_QUEUES = (
    Queue("split", DEFAULT_EXCHANGE, routing_key="split", priority=0),
    Queue("georeference", DEFAULT_EXCHANGE, routing_key="georeference", priority=0),
    Queue("map", DEFAULT_EXCHANGE, routing_key="map", priority=0),
    Queue("mosaic", DEFAULT_EXCHANGE, routing_key="mosaic", priority=0),
    Queue("housekeeping", DEFAULT_EXCHANGE, routing_key="housekeeping", priority=0),
)

CELERY_TASK_ROUTES = {
    "ohmg.georeference.tasks.run_preparation_session": {"queue": "split"},
    "ohmg.georeference.tasks.bulk_run_preparation_sessions": {"queue": "split"},
    "ohmg.georeference.tasks.run_georeference_session": {"queue": "georeference"},
    "ohmg.georeference.tasks.delete_stale_sessions": {"queue": "housekeeping"},
    "ohmg.georeference.tasks.delete_preview_vrts": {"queue": "housekeeping"},
    "ohmg.georeference.tasks.create_mosaic_cog": {"queue": "mosaic"},
    "ohmg.core.tasks.load_map_documents_as_task": {"queue": "map"},
    "ohmg.core.tasks.load_document_file_as_task": {"queue": "map"},
}

# empty celery beat schedule of default GeoNode jobs
CELERY_BEAT_SCHEDULE = {
    "remove_stale_sessions": {
        "task": "ohmg.georeference.tasks.delete_stale_sessions",
        "schedule": 60.0,
    }
}

# note: this is app_label.ModelClass,
AUTH_USER_MODEL = "accounts.User"
# while this is a module path to the adapter class
ACCOUNT_ADAPTER = "ohmg.accounts.adapter.AccountAdapter"

ACCOUNT_FORMS = {"signup": "ohmg.accounts.forms.OHMGSignupForm"}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_REDIRECT_URL = "/"
ACCOUNT_USERNAME_VALIDATORS = "ohmg.accounts.validators.custom_username_validators"

# prep/georef session duration before expiration (seconds)
GEOREFERENCE_SESSION_LENGTH = int(os.getenv("GEOREFERENCE_SESSION_LENGTH", 600))

MAPBOX_API_TOKEN = os.environ.get("MAPBOX_API_TOKEN", None)

# no trailing slash on server location
IIIF_SERVER_ENABLED = False
IIIF_SERVER_LOCATION = "http://localhost:8182"

# To allow other sites to read IIIF resources set CORS_ORIGIN_ALLOW_ALL to True
CORS_ORIGIN_ALLOW_ALL = False

# Doubling this to 480, 400 (2/1/24) to present higher fidelity cover pages.
DEFAULT_MAX_THUMBNAIL_DIMENSION = 400
DEFAULT_THUMBNAIL_SIZE = (480, 400)

# Location of locale files
LOCALE_PATHS = (PROJECT_DIR / "locale",)

OHMG_IMPORTERS = {
    "map": {
        "default": "ohmg.core.importer.DefaultImporter",
        "loc-sanborn": "ohmg.extensions.loc_sanborn.LOCSanbornImporter",
        "dsl": "ohmg.extensions.dsl.DSLFileImporter",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(funcName)s %(process)d " "%(message)s"
        },
        "moderate": {"format": "%(levelname)s %(asctime)s %(module)s %(message)s"},
        "simple": {
            "format": "%(message)s",
        },
    },
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        ## haven't gotten this to work yet
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "info": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "info.log"),
            "formatter": "moderate",
        },
        "warning": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "warning.log"),
            "formatter": "moderate",
        },
        "error": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "error.log"),
            "formatter": "moderate",
        },
        "ohmg-debug": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "ohmg-debug.log"),
            "formatter": "moderate",
        },
        "georeference-debug": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "georeference-debug.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "ohmg.georeference": {
            "handlers": ["georeference-debug"],
            "level": "DEBUG",
        },
        "ohmg": {
            "handlers": ["ohmg-debug", "info", "warning", "error"],
            "level": "DEBUG",
        },
    },
}

# cleanup some celery logging as suggested here:
# https://stackoverflow.com/a/20719461/3873885
if DEBUG:
    celery_log_level = "DEBUG"
    LOGGING["loggers"]["ohmg"]["handlers"].append("console")
    LOGGING["loggers"]["ohmg.georeference"]["handlers"].append("console")
else:
    celery_log_level = "INFO"

## TODO: figure out if this setting can fix what the list below are supposed to fix
# CELERYD_HIJACK_ROOT_LOGGER = False

LOGGING["loggers"]["celery"] = {
    "handlers": ["console"],
    "level": celery_log_level,
    "propagate": True,
}
for i in ["worker", "concurrency", "beat"]:
    LOGGING["loggers"]["celery." + i] = {
        "handlers": [],
        "level": "WARNING",
        "propagate": True,
    }
for i in ["job", "consumer", "mediator", "control", "bootsteps"]:
    LOGGING["loggers"]["celery.worker." + i] = {
        "handlers": [],
        "level": "WARNING",
        "propagate": True,
    }
