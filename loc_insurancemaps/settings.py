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

# Load all default geonode settings
from geonode.settings import *

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

# This must be the name of the directory holding this file (i.e. the app name)
PROJECT_NAME = os.path.basename(LOCAL_ROOT)
WSGI_APPLICATION = f"{PROJECT_NAME}.wsgi.application"

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith('/'):
    SITEURL = '{}/'.format(SITEURL)

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
    'modeltranslation',
    'dal',
    'dal_select2',
    'grappelli',
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
    'dj_pagination',
    'taggit',
    'treebeard',
    'leaflet',
    'bootstrap3_datetime',
    'django_filters',
    'mptt',
    'storages',
    'floppyforms',
    'tinymce',
    'widget_tweaks',
    'django_extensions',
    'rest_framework',
    'rest_framework_gis',
    'dynamic_rest',
    'drf_spectacular',
    'django_forms_bootstrap',
    'avatar',
    'dialogos',
    'pinax.ratings',
    'announcements',
    'actstream',
    'user_messages',
    'tastypie',
    'polymorphic',
    'guardian',
    'oauth2_provider',
    'corsheaders',
    'invitations',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'geonode',
    'markdownify',
    'geonode.api',
    'geonode.base',
    'geonode.br',
    'geonode.layers',
    'geonode.maps',
    'geonode.geoapps',
    'geonode.documents',
    'geonode.security',
    'geonode.catalogue',
    'geonode.catalogue.metadataxsl',
    'geonode.people',
    'geonode.client',
    'geonode.themes',
    'geonode.proxy',
    'geonode.social',
    'geonode.groups',
    'geonode.services',
    'geonode.geoserver',
    'geonode.upload',
    'geonode.tasks',
    'geonode.messaging',
    'geonode.monitoring',
    'geonode.documents.exif',
    'geonode.favorite',
    'mapstore2_adapter',
    'mapstore2_adapter.geoapps',
    'mapstore2_adapter.geoapps.geostories',
    'geonode_mapstore_client',
    'pinax.notifications',
]

INSTALLED_APPS += (
    'django_svelte',
    'georeference',
    PROJECT_NAME,
)

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
    'geonode.base.middleware.MaintenanceMiddleware',
    'geonode.base.middleware.ReadOnlyMiddleware',
    'geonode.security.middleware.SessionControlMiddleware',
)

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE = ('debug_toolbar.middleware.DebugToolbarMiddleware', ) + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']

USE_TITILER = ast.literal_eval(os.getenv("USE_TITILER", True))
TITILER_HOST = os.getenv("TITILER_HOST", "")

MEDIA_HOST = os.getenv("MEDIA_HOST", SITEURL)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_CONFIG = {
    "aws_access_key_id": os.getenv("S3_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("S3_SECRET_ACCESS_KEY"),
    "endpoint_url": os.getenv("S3_ENDPOINT_URL"),
}

# conditionally add static files from the 'georeference' app, as well as
# Mapserver information, used for the georeferencing preview layer
if 'georeference' in INSTALLED_APPS:
    TEMPLATES[0]['DIRS'].insert(0, os.path.join(os.path.dirname(LOCAL_ROOT), "georeference", "templates"))
    STATICFILES_DIRS.append(os.path.join(os.path.dirname(LOCAL_ROOT), "georeference", "static"))
    # this is the path for the svelte components
    STATICFILES_DIRS.append(os.path.join(os.path.dirname(LOCAL_ROOT), "georeference", "components", "public", "build"))

    # must have trailing slash
    MAPSERVER_ENDPOINT = os.getenv("MAPSERVER_ENDPOINT", "http://localhost:9999/wms/")
    MAPSERVER_MAPFILE = os.path.join(LOCAL_ROOT, "mapserver.map")

    MIDDLEWARE += ("georeference.middleware.GeoreferenceMiddleware", )
    TEMPLATES[0]['OPTIONS']['context_processors'].append("georeference.context_processors.georeference_info")

    CELERY_BEAT_SCHEDULE['delete_expired_sessions'] = {
        'task': 'georeference.tasks.delete_expired_sessions',
        'schedule': 60.0,
    }

    # prep/georef/trim session duration before expiration (seconds)
    GEOREFERENCE_SESSION_LENGTH = 600

# add static files and templates that are in the local (loc_insurancemaps) app
TEMPLATES[0]['DIRS'].insert(0, os.path.join(LOCAL_ROOT, "templates"))
STATICFILES_DIRS.append(os.path.join(LOCAL_ROOT, "static"))
STATICFILES_DIRS.append(os.path.join(LOCAL_ROOT, "components", "public", "build"))
# add context processor and middleware
TEMPLATES[0]['OPTIONS']['context_processors'].append("loc_insurancemaps.context_processors.loc_info")
MIDDLEWARE += ("loc_insurancemaps.middleware.LOCMiddleware", )

# exclude many default profile fields to reduce to identifiable personal information
PROFILE_EDIT_EXCLUDE_FIELD = [
    "first_name",
    "last_name",
    "profile",
    "voice",
    "fax",
    "delivery",
    "city",
    "area",
    "zipcode",
    "country",
    "keywords",
    "language",
]

# disable unnecessary search filters for cleaner interface
SEARCH_FILTERS = {
    'TEXT_ENABLED': True,
    'TYPE_ENABLED': True,
    'CATEGORIES_ENABLED': False,
    'OWNERS_ENABLED': False,
    'KEYWORDS_ENABLED': False,
    'H_KEYWORDS_ENABLED': False,
    'T_KEYWORDS_ENABLED': True,
    'DATE_ENABLED': True,
    'REGION_ENABLED': True,
    'EXTENT_ENABLED': True,
    'GROUPS_ENABLED': False,
    'GROUP_CATEGORIES_ENABLED': False,
}

# no trailing slash on server location
IIIF_SERVER_ENABLED = False
IIIF_SERVER_LOCATION = "http://localhost:8182"

# To allow other sites to read IIIF resources set CORS_ORIGIN_ALLOW_ALL to True
CORS_ORIGIN_ALLOW_ALL = False

# the default thumbnail background is wikimedia and it causes a lot of errors
# set to custom blank background handler here.
THUMBNAIL_BACKGROUND = { "class": "loc_insurancemaps.background.NoThumbnailBackground" }

DEFAULT_THUMBNAIL_SIZE = (240, 200)

# Location of url mappings
ROOT_URLCONF = os.getenv('ROOT_URLCONF', '{}.urls'.format(PROJECT_NAME))

# Location of locale files
LOCALE_PATHS = (
    os.path.join(LOCAL_ROOT, 'locale'),
    ) + LOCALE_PATHS

loaders = TEMPLATES[0]['OPTIONS'].get('loaders') or ['django.template.loaders.filesystem.Loader','django.template.loaders.app_directories.Loader']
TEMPLATES[0]['OPTIONS']['loaders'] = loaders
TEMPLATES[0].pop('APP_DIRS', None)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(funcName)s %(process)d '
                      '%(thread)d %(message)s'
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

CENTRALIZED_DASHBOARD_ENABLED = ast.literal_eval(os.getenv('CENTRALIZED_DASHBOARD_ENABLED', 'False'))
if CENTRALIZED_DASHBOARD_ENABLED and USER_ANALYTICS_ENABLED and 'geonode_logstash' not in INSTALLED_APPS:
    INSTALLED_APPS += ('geonode_logstash',)

    CELERY_BEAT_SCHEDULE['dispatch_metrics'] = {
        'task': 'geonode_logstash.tasks.dispatch_metrics',
        'schedule': 3600.0,
    }

LDAP_ENABLED = ast.literal_eval(os.getenv('LDAP_ENABLED', 'False'))
if LDAP_ENABLED and 'geonode_ldap' not in INSTALLED_APPS:
    INSTALLED_APPS += ('geonode_ldap',)

# Add your specific LDAP configuration after this comment:
# https://docs.geonode.org/en/master/advanced/contrib/#configuration

API_LIMIT_PER_PAGE = 20
CLIENT_RESULTS_LIMIT = 20

# don't use MAPBOX_ACCESS_TOKEN because it will be picked up by GeoNode and
# trigger many Mapbox-based basemaps. Instead use MAPBOX_API_TOKEN here and
# manually replace the sentinel imagery basemap with Mapbox Satellite.
MAPBOX_API_TOKEN = os.environ.get('MAPBOX_API_TOKEN', None)
if MAPBOX_API_TOKEN:
    MAPBOX_SATELLITE_SOURCE = "satellite-streets-v10"
    MAPBOX_SATELLITE_LAYER = {
        'type': 'tileprovider',
        'title': 'MapBox Satellite',
        'provider': 'MapBoxStyle',
        'name': 'MapBox Satellite',
        'accessToken': MAPBOX_API_TOKEN,
        'source': MAPBOX_SATELLITE_SOURCE,
        'thumbURL': f'https://api.mapbox.com/styles/v1/mapbox/{MAPBOX_SATELLITE_SOURCE}/tiles/256/6/33/23?access_token={MAPBOX_API_TOKEN}',
        'group': 'background',
        'visibility': False,
    }
    MAPSTORE_BASELAYERS = [i for i in DEFAULT_MS2_BACKGROUNDS if not i.get('id') == "s2cloudless"]
    MAPSTORE_BASELAYERS.insert(2, MAPBOX_SATELLITE_LAYER)
