# -*- coding:utf-8 -*-
#
# Copyright 2013 NAMD-EMAP-FGV
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

import ConfigParser

from pypln.web.settings.base import *

DEBUG = False

ADMINS = [
    ("pypln", "pyplnproject@gmail.com"),
]

MANAGERS = ADMINS

SERVE_MEDIA = False
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static_files")

pgpass_file_path = os.path.expanduser("~/.pgpass")
secret_key_file_path = os.path.expanduser("~/.secret_key")
smtp_config_file_path = os.path.expanduser("~/.smtp_config")
allowed_hosts_file_path = os.path.expanduser("~/.pypln_allowed_hosts")

if os.path.exists(smtp_config_file_path):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_USE_TLS = True
    with open(smtp_config_file_path, 'r') as smtp_config_file:
        EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD = smtp_config_file.read().strip().split(':')

with open(secret_key_file_path, 'r') as secret_key_file:
    SECRET_KEY = secret_key_file.read().strip()

with open(pgpass_file_path, 'r') as pgpass_file:
    pg_credentials = pgpass_file.read().strip()

db_host, db_port, db_name, db_user, db_password = pg_credentials.split(":")

with open(allowed_hosts_file_path, 'r') as allowed_hosts_file:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_file.readlines()]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": db_name,
        "USER": db_user,
        "PASSWORD": db_password,
        "HOST": db_host,
        "PORT": db_port,
    }
}

#TODO: read router configuration from a config file (issue #14)
ROUTER_API = 'tcp://127.0.0.1:5555'
ROUTER_BROADCAST = 'tcp://127.0.0.1:5556'
ROUTER_TIMEOUT = 5


def get_store_config():
    """Code originally from pypln.backend.router"""

    config_filename = os.path.expanduser('~/.pypln_store_config')
    defaults = {'host': 'localhost',
                'port': '27017',
                'database': 'pypln',
                'analysis_collection': 'analysis',
                'gridfs_collection': 'files',
                'monitoring_collection': 'monitoring',
    }
    config = ConfigParser.ConfigParser(defaults=defaults)
    config.add_section('store')
    config.read(config_filename)
    store_config = dict(config.items('store'))
    # The database port needs to be an integer, but ConfigParser will treat
    # everything as a string unless you use the specific method to retrieve the
    # value.
    store_config['port'] = config.getint('store', 'port')
    return store_config

MONGODB_CONFIG = get_store_config()


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
