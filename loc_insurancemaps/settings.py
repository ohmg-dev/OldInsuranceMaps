# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Django settings for the GeoNode project.
import ast
import os
import dj_database_url

from kombu import Queue, Exchange

# Load all default geonode settings
# from geonode.settings import *

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.getenv("SECRET_KEY")
WSGI_APPLICATION = "loc_insurancemaps.wsgi.application"

DEBUG = True

# add trailing slash to site url. geoserver url will be relative to this
SITEURL = os.getenv("SITEURL", "http://localhost:8000")
if not SITEURL.endswith('/'):
    SITEURL = '{}/'.format(SITEURL)

SITE_ID = int(os.getenv('SITE_ID', '1'))
SITENAME = os.getenv("SITENAME", 'Example.com')

# Set path to cache directory
CACHE_DIR = os.path.join(LOCAL_ROOT, "cache")
TEMP_DIR = os.path.join(LOCAL_ROOT, "temp")
LOG_DIR = os.path.join(LOCAL_ROOT, "logs")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', "en")

## overwrite geonode installed apps to begin paring them down
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.gis',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'accounts',

    'modeltranslation',
    'dal',
    'dal_select2',
    # 'grappelli',
    'dj_pagination',
    'taggit',
    'treebeard',
    # 'leaflet',
    'bootstrap3_datetime',
    'django_filters',
    'mptt',
    'storages',
    'floppyforms',
    # 'tinymce',
    'widget_tweaks',
    'django_extensions',
    # 'rest_framework',
    # 'rest_framework_gis',
    # 'dynamic_rest',
    'drf_spectacular',
    'django_forms_bootstrap',
    'avatar',
    'dialogos',
    'pinax.ratings',
    'announcements',
    'actstream',
    'user_messages',
    # 'tastypie',
    'polymorphic',
    'guardian',
    # 'oauth2_provider',
    'corsheaders',
    'invitations',
    # 'geonode',
    # 'markdownify',
    # 'geonode.api', # needed in geonode.base
    # 'geonode.base',
    # 'geonode.br',
    # 'geonode.layers',
    # 'geonode.maps',
    # 'geonode.geoapps',
    # 'geonode.documents',
    # 'geonode.security',
    # 'geonode.catalogue',
    # 'geonode.catalogue.metadataxsl',
    # 'geonode.people',
    # 'geonode.client',
    # 'geonode.themes',
    # 'geonode.proxy',
    # 'geonode.social',
    # 'geonode.groups',
    # 'geonode.services', # error when removing this app still
    # 'geonode.geoserver', # needed by geonode.api
    # 'geonode.upload', # needed to delete users (attached to profile??)
    # 'geonode.tasks',
    # 'geonode.messaging',
    # 'geonode.monitoring', # needed to delete users (attached to profile??)
    # 'geonode.documents.exif',
    # 'geonode.favorite', # needed to delete users (attached to profile??)
    # 'mapstore2_adapter',
    # 'mapstore2_adapter.geoapps',
    # 'mapstore2_adapter.geoapps.geostories',
    # 'geonode_mapstore_client',
    'pinax.notifications',
]

AUTH_USER_MODEL = 'accounts.User'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptPasswordHasher',
]

INSTALLED_APPS += (
    'georeference',
    'loc_insurancemaps',
    'frontend',
    'places',
    # 'accounts',
)

TEMPLATES = [
  {
    "NAME": "Project Templates",
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [
      os.path.join(os.path.dirname(LOCAL_ROOT), "frontend", "templates"),
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
        "django.contrib.auth.context_processors.auth",
        "loc_insurancemaps.context_processors.loc_info"
      ],
      "debug": DEBUG,
    }
  }
]

DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=0
    )
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(os.path.dirname(LOCAL_ROOT), "frontend", "static"),
    os.path.join(os.path.dirname(LOCAL_ROOT), "frontend", "components", "public", "build"),
]

AUTHENTICATION_BACKENDS = [
  "django.contrib.auth.backends.ModelBackend",
  "guardian.backends.ObjectPermissionBackend",
  "allauth.account.auth_backends.AuthenticationBackend",
  "announcements.auth_backends.AnnouncementPermissionsBackend"
]

ENABLE_NEWSLETTER = os.getenv("ENABLE_NEWSLETTER", False)
if ENABLE_NEWSLETTER:
    INSTALLED_APPS += (
        'sorl.thumbnail',
        'newsletter',
    )
    NEWSLETTER_THUMBNAIL = 'sorl-thumbnail'
    NEWSLETTER_CONFIRM_EMAIL_SUBSCRIBE = True
    NEWSLETTER_CONFIRM_EMAIL_UNSUBSCRIBE = False
    NEWSLETTER_CONFIRM_EMAIL_UPDATE = False

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@localhost")

MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'dj_pagination.middleware.PaginationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    # 'geonode.base.middleware.MaintenanceMiddleware',
    # 'geonode.base.middleware.ReadOnlyMiddleware',
    # 'geonode.security.middleware.SessionControlMiddleware',
)

ENABLE_CPROFILER = ast.literal_eval(os.getenv("ENABLE_CPROFILER", False))
if ENABLE_CPROFILER:
    MIDDLEWARE += ('django_cprofile_middleware.middleware.ProfilerMiddleware', )

ENABLE_DEBUG_TOOLBAR = ast.literal_eval(os.getenv("ENABLE_DEBUG_TOOLBAR", False))
if DEBUG and ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE = ('debug_toolbar.middleware.DebugToolbarMiddleware', ) + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']

TITILER_HOST = os.getenv("TITILER_HOST", "")

MEDIA_HOST = os.getenv("MEDIA_HOST", SITEURL)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_CONFIG = {
    "aws_access_key_id": os.getenv("S3_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("S3_SECRET_ACCESS_KEY"),
    "endpoint_url": os.getenv("S3_ENDPOINT_URL"),
}

VIEWER_SHOWCASE_SLUG = os.getenv("VIEWER_SHOWCASE_SLUG")

# this is a hack to handle the fact that certain GDAL and Django versions
# are not compatible, and the order of lat/long gets messed up. ONLY to
# be used in development!!!!
# this will be removed once Django is upgraded
SWAP_COORDINATE_ORDER = ast.literal_eval(os.getenv("SWAP_COORDINATE_ORDER", False))

# setup frontend app
# TEMPLATES[0]['DIRS'].insert(0, os.path.join(os.path.dirname(LOCAL_ROOT), "frontend", "templates"))
# STATICFILES_DIRS += [
#     os.path.join(os.path.dirname(LOCAL_ROOT), "frontend", "static"),
#     os.path.join(os.path.dirname(LOCAL_ROOT), "frontend", "components", "public", "build"),
# ]

# CONFIGURE CELERY
CELERY_BROKER_URL = os.getenv('BROKER_URL')
print(CELERY_BROKER_URL)
CELERY_RESULT_BACKEND = f'file:///{os.path.join(LOCAL_ROOT, ".celery_results")}'

# basic independent setup for Celery Exchange/Queue
DEFAULT_EXCHANGE = Exchange('default', type='topic')
# CELERY_TASK_QUEUES += (
CELERY_TASK_QUEUES = (
    Queue('split', DEFAULT_EXCHANGE, routing_key='split', priority=0),
    Queue('georeference', DEFAULT_EXCHANGE, routing_key='georeference', priority=0),
    Queue('volume', DEFAULT_EXCHANGE, routing_key='volume', priority=0),
    Queue('mosaic', DEFAULT_EXCHANGE, routing_key='mosaic', priority=0),
    Queue('housekeeping', DEFAULT_EXCHANGE, routing_key='housekeeping', priority=0),
)

CELERY_TASK_ROUTES = {
    'georeference.tasks.run_preparation_session': {'queue': 'split'},
    'georeference.tasks.run_georeference_session': {'queue': 'georeference'},
    'georeference.tasks.delete_expired': {'queue': 'housekeeping'},
    'loc_insurancemaps.tasks.load_docs_as_task': {'queue': 'volume'},
    'loc_insurancemaps.tasks.generate_mosaic_geotiff_as_task': {'queue': 'mosaic'},
}

# empty celery beat schedule of default GeoNode jobs
CELERY_BEAT_SCHEDULE = {
    'delete_expired_sessions': {
        'task': 'georeference.tasks.delete_expired',
        'schedule': 60.0,
    }
}


# must have trailing slash
MAPSERVER_ENDPOINT = os.getenv("MAPSERVER_ENDPOINT", "http://localhost:9999/wms/")
MAPSERVER_MAPFILE = os.path.join(LOCAL_ROOT, "mapserver.map")

# prep/georef session duration before expiration (seconds)
GEOREFERENCE_SESSION_LENGTH = int(os.getenv("GEOREFERENCE_SESSION_LENGTH", 600))

# no trailing slash on server location
IIIF_SERVER_ENABLED = False
IIIF_SERVER_LOCATION = "http://localhost:8182"

# To allow other sites to read IIIF resources set CORS_ORIGIN_ALLOW_ALL to True
CORS_ORIGIN_ALLOW_ALL = False

DEFAULT_THUMBNAIL_SIZE = (240, 200)

# Location of url mappings
ROOT_URLCONF = 'loc_insurancemaps.urls'

# Location of locale files
LOCALE_PATHS = (
    os.path.join(LOCAL_ROOT, 'locale'),
) #+ LOCALE_PATHS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(funcName)s %(process)d '
                      '%(message)s'
        },
        'moderate': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'console-vb': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        ## haven't gotten this to work yet
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'geonode': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'geonode.log'),
            'formatter': 'moderate',
        },
        'info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'info.log'),
            'formatter': 'moderate',
        },
        'georeference-debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'georeference-debug.log'),
            'formatter': 'verbose',
        },
        'loc_insurancemaps-debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'loc_insurancemaps-debug.log'),
            'formatter': 'verbose',
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"], "level": "ERROR", },
        "geonode": {
            "handlers": ["geonode"], "level": "DEBUG", },
        "geoserver-restconfig.catalog": {
            "handlers": ["console"], "level": "ERROR", },
        "owslib": {
            "handlers": ["console"], "level": "ERROR", },
        "pycsw": {
            "handlers": ["console"], "level": "ERROR", },
        "celery": {
            "handlers": ["console"], "level": "DEBUG", },
        "mapstore2_adapter.plugins.serializers": {
            "handlers": ["console"], "level": "DEBUG", },
        "geonode_logstash.logstash": {
            "handlers": ["console"], "level": "DEBUG", },
        # logging for this app specifically
        "georeference.tests": {
            "handlers": ["console"], "level": "DEBUG", },
        "georeference": {
            "handlers": ["info", "georeference-debug"], "level": "DEBUG", },
        "loc_insurancemaps": {
            "handlers": ["info", "loc_insurancemaps-debug"], "level": "DEBUG", },
    },
}

# cleanup some celery logging as suggested here:
# https://stackoverflow.com/a/20719461/3873885
if DEBUG:
    celery_log_level = 'DEBUG'
else:
    celery_log_level = 'INFO'

LOGGING['loggers']['celery'] = {
    'handlers': ['console'],
    'level': celery_log_level,
    'propagate': True,
}
for i in ['worker', 'concurrency', 'beat']:
    LOGGING['loggers']['celery.' + i] = {
        'handlers': [],
        'level': 'WARNING',
        'propagate': True,
    }
for i in ['job', 'consumer', 'mediator', 'control', 'bootsteps']:
    LOGGING['loggers']['celery.worker.' + i] = {
        'handlers': [],
        'level': 'WARNING',
        'propagate': True,
    }

# CENTRALIZED_DASHBOARD_ENABLED = ast.literal_eval(os.getenv('CENTRALIZED_DASHBOARD_ENABLED', 'False'))
# if CENTRALIZED_DASHBOARD_ENABLED and USER_ANALYTICS_ENABLED and 'geonode_logstash' not in INSTALLED_APPS:
#     INSTALLED_APPS += ('geonode_logstash',)

#     CELERY_BEAT_SCHEDULE['dispatch_metrics'] = {
#         'task': 'geonode_logstash.tasks.dispatch_metrics',
#         'schedule': 3600.0,
#     }

# LDAP_ENABLED = ast.literal_eval(os.getenv('LDAP_ENABLED', 'False'))
# if LDAP_ENABLED and 'geonode_ldap' not in INSTALLED_APPS:
#     INSTALLED_APPS += ('geonode_ldap',)

# Add your specific LDAP configuration after this comment:
# https://docs.geonode.org/en/master/advanced/contrib/#configuration

# API_LIMIT_PER_PAGE = 20
# CLIENT_RESULTS_LIMIT = 20

# # don't use MAPBOX_ACCESS_TOKEN because it will be picked up by GeoNode and
# # trigger many Mapbox-based basemaps. Instead use MAPBOX_API_TOKEN here and
# # manually replace the sentinel imagery basemap with Mapbox Satellite.
MAPBOX_API_TOKEN = os.environ.get('MAPBOX_API_TOKEN', None)
# if MAPBOX_API_TOKEN:
#     MAPBOX_SATELLITE_SOURCE = "satellite-streets-v10"
#     MAPBOX_SATELLITE_LAYER = {
#         'type': 'tileprovider',
#         'title': 'MapBox Satellite',
#         'provider': 'MapBoxStyle',
#         'name': 'MapBox Satellite',
#         'accessToken': MAPBOX_API_TOKEN,
#         'source': MAPBOX_SATELLITE_SOURCE,
#         'thumbURL': f'https://api.mapbox.com/styles/v1/mapbox/{MAPBOX_SATELLITE_SOURCE}/tiles/256/6/33/23?access_token={MAPBOX_API_TOKEN}',
#         'group': 'background',
#         'visibility': False,
#     }
#     MAPSTORE_BASELAYERS = [i for i in DEFAULT_MS2_BACKGROUNDS if not i.get('id') == "s2cloudless"]
#     MAPSTORE_BASELAYERS.insert(2, MAPBOX_SATELLITE_LAYER)
