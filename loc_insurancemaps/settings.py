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

INSTALLED_APPS += (
    'django_svelte',
    'georeference',
    PROJECT_NAME,
)

# add static files and templates that are in the local (loc_insurancemaps) app
TEMPLATES[0]['DIRS'].insert(0, os.path.join(LOCAL_ROOT, "templates"))
STATICFILES_DIRS.append(os.path.join(LOCAL_ROOT, "static"))
STATICFILES_DIRS.append(os.path.join(LOCAL_ROOT, "components", "public", "build"))
# add context processor
TEMPLATES[0]['OPTIONS']['context_processors'].append("loc_insurancemaps.context_processors.loc_info")

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

# no trailing slash on server location
IIIF_SERVER_ENABLED = False
IIIF_SERVER_LOCATION = "http://localhost:8182"

# To allow other sites to read IIIF resources set CORS_ORIGIN_ALLOW_ALL to True
CORS_ORIGIN_ALLOW_ALL = False

# the default thumbnail background is wikimedia and it causes a lot of errors
# set to custom blank background handler here.
THUMBNAIL_BACKGROUND = { "class": "loc_insurancemaps.background.NoThumbnailBackground" }

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
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s'
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
            'formatter': 'simple'
        },
        'console-vb': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'info.log')
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"], "level": "ERROR", },
        "geonode": {
            "handlers": ["console", "file"], "level": "INFO", },
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
        "georeference.tests": {
            "handlers": ["console"], "level": "DEBUG", },
    },
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
