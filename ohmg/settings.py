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
try:
    from urllib.parse import urlparse, urlunparse
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
    from urlparse import urlparse, urlunparse

# Load all default geonode settings
from geonode.settings import *

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

# This must be the name of the directory holding this file (i.e. the app name)
PROJECT_NAME = os.path.basename(LOCAL_ROOT)
WSGI_APPLICATION = "{}.wsgi.application".format(PROJECT_NAME)

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith('/'):
    SITEURL = '{}/'.format(SITEURL)

SITENAME = os.getenv("SITENAME", 'OHMG')

# Set path to cache directory
CACHE_DIR = os.path.join(LOCAL_ROOT, "cache")
TEMP_DIR = os.path.join(LOCAL_ROOT, "temp")
LOG_DIR = os.path.join(LOCAL_ROOT, "logs")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', "en")

if PROJECT_NAME not in INSTALLED_APPS:
    INSTALLED_APPS += (PROJECT_NAME, )

if 'georeference' not in INSTALLED_APPS:
    INSTALLED_APPS += ('georeference', )

if 'lc_insurancemaps' not in INSTALLED_APPS:
    INSTALLED_APPS += ('lc_insurancemaps', )

GEOREFERENCE_ENABLED = True

# must have trailing slash
MAPSERVER_ENDPOINT = "http://localhost:9999/wms/"
MAPSERVER_MAPFILE = os.path.join(LOCAL_ROOT, "mapserver.map")

# no trailing slash on server location
IIIF_SERVER_ENABLED = False
IIIF_SERVER_LOCATION = "http://localhost:8182"

# To allow other sites to read IIIF resources set CORS_ORIGIN_ALLOW_ALL to True
CORS_ORIGIN_ALLOW_ALL = False

# Location of url mappings
ROOT_URLCONF = os.getenv('ROOT_URLCONF', '{}.urls'.format(PROJECT_NAME))

# Location of locale files
LOCALE_PATHS = (
    os.path.join(LOCAL_ROOT, 'locale'),
    ) + LOCALE_PATHS

# add static files and templates that are in the local app
STATICFILES_DIRS.append(os.path.join(LOCAL_ROOT, "static"))
TEMPLATES[0]['DIRS'].insert(0, os.path.join(LOCAL_ROOT, "templates"))


loaders = TEMPLATES[0]['OPTIONS'].get('loaders') or ['django.template.loaders.filesystem.Loader','django.template.loaders.app_directories.Loader']
# loaders.insert(0, 'apptemplates.Loader')
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

# this setting is a little squirrely... not sure the best place to set it
MEDIA_ROOT = os.getenv("MEDIA_ROOT", MEDIA_ROOT)

try:
    from .local_settings import *
except ImportError:
    pass

# add templates based on installed apps. Doing so here allows local_settings.py
# to determine this installation's apps

# conditionally add static files from the 'georefernce' app
if 'georeference' in INSTALLED_APPS:
    INSTALLED_APPS += ('django_svelte', )
    TEMPLATES[0]['DIRS'].insert(0, os.path.join(os.path.dirname(LOCAL_ROOT), "georeference", "templates"))
    TEMPLATES[0]['OPTIONS']['context_processors'].append('georeference.context_processors.georeference_info')
    STATICFILES_DIRS.append(os.path.join(os.path.dirname(LOCAL_ROOT), "georeference", "static"))
    # this is the path for the svelte components
    STATICFILES_DIRS.append(os.path.join(os.path.dirname(LOCAL_ROOT), "georeference", "components", "public", "build"))

# conditionally add static files and templates from the 'lc_insurancemaps' app
if 'lc_insurancemaps' in INSTALLED_APPS:
    TEMPLATES[0]['DIRS'].insert(0, os.path.join(os.path.dirname(LOCAL_ROOT), "lc_insurancemaps", "templates"))
    STATICFILES_DIRS.append(os.path.join(os.path.dirname(LOCAL_ROOT), "lc_insurancemaps", "static"))
    STATICFILES_DIRS.append(os.path.join(os.path.dirname(LOCAL_ROOT), "lc_insurancemaps", "components", "public", "build"))
    TEMPLATES[0]['OPTIONS']['context_processors'].append('lc_insurancemaps.context_processors.lc_svelte_params')

UPLOADER = {
    'BACKEND': os.getenv('DEFAULT_BACKEND_UPLOADER', 'geonode.rest'),
    'OPTIONS': {
        'TIME_ENABLED': False,
        'MOSAIC_ENABLED': True,
    },
    'SUPPORTED_CRS': [
        'EPSG:4326',
        'EPSG:3785',
        'EPSG:3857',
        'EPSG:32647',
        'EPSG:32736'
    ],
    'SUPPORTED_EXT': [
        '.shp',
        '.csv',
        '.kml',
        '.kmz',
        '.json',
        '.geojson',
        '.tif',
        '.tiff',
        '.geotiff',
        '.gml',
        '.xml',
        '.vrt',
    ]
}