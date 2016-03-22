#!/bin/bash
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

PYPLN_HOME="/srv/pypln"
NUM_WORKERS=8
WSGI_HOST="127.0.0.1"
WSGI_PORT="8000"
ERRLOG="$PYPLN_HOME/logs/wsgi_server.err"
ACCESS_LOG="$PYPLN_HOME/logs/wsgi_server.access"
SETTINGS="settings.production"

source "$PYPLN_HOME/project/bin/activate"

# Supervisord is not passing $HOME to this script, and because of that we get
# errors like trying to use "//.python-eggs" as PYTHON_EGG_CACHE
export HOME=$PYPLN_HOME
exec gunicorn -w $NUM_WORKERS -b $WSGI_HOST:$WSGI_PORT --error-logfile=$ERRLOG --access-logfile=$ACCESS_LOG pypln.web.wsgi:application
