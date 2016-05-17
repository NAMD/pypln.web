# -*- coding:utf-8 -*-
#
# Copyright 2012 NAMD-EMAP-FGV
#
# This file is part of PyPLN. You can get more information at: http://pypln.org/.
#
# PyPLN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyPLN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyPLN.  If not, see <http://www.gnu.org/licenses/>.
import os

from decouple import config, Csv
from dj_database_url import parse as db_url

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


def split_uris(uri):
    return uri.split(';')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))

DEBUG = config('DEBUG', default=False, cast=bool)
TEMPLATE_DEBUG = DEBUG

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

if EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
    EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD = config('EMAIL_CONFIG', default='example_host,25,username,password', cast=Csv())
    EMAIL_PORT = int(EMAIL_PORT)
    EMAIL_USE_TLS = True


ADMINS = (
    config('ADMIN', cast=Csv())
)

MANAGERS = ADMINS

DATABASES = {
    'default': config('DATABASE_URL', default='sqlite:///dev.db', cast=db_url)
}

MONGODB_URIS = config('MONGODB_URIS', default='mongodb://localhost:27017',
        cast=split_uris)

MONGODB_DBNAME = config('MONGODB_DBNAME', default='pypln')
MONGODB_COLLECTION = config('MONGODB_COLLECTION', default='analysis')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static_files')

STATIC_URL = '/static/'

STATICFILES_DIRS = (
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = config('SECRET_KEY')

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request"
)

ROOT_URLCONF = 'pypln.web.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'pypln.web.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'rest_framework',
    'rest_framework.authtoken',
    'registration',

    'pypln.web.core',
    'pypln.web.backend_adapter',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

ACCOUNT_ACTIVATION_DAYS = 7

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    "PAGINATE_BY": 100,
    "PAGINATE_BY_PARAM": "page_size",
}


ELASTICSEARCH_CONFIG = {
    'hosts': config('ELASTICSEARCH_HOSTS', default='127.0.0.1', cast=Csv()),
}

SERVE_MEDIA = config('SERVE_MEDIA', default=False, cast=bool)

if not DEBUG:
    from django.core.exceptions import SuspiciousOperation

    def skip_suspicious_operations(record):
        if record.exc_info:
            exc = record.exc_info[1]
            if isinstance(exc, SuspiciousOperation):
                return False
        return True

    LOGGING['filters']['skip_suspicious_operations'] = {
        '()': 'django.utils.log.CallbackFilter',
        'callback': skip_suspicious_operations,
    }

    LOGGING['handlers']['mail_admins']['filters'].append('skip_suspicious_operations')
