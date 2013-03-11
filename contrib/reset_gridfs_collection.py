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
import sys

from pypln.web.core.models import Document, gridfs_storage
from pypln.web.backend_adapter.pipelines import create_pipeline

if 'dev' not in gridfs_storage.database:
    error_message = ("We expect the mongodb database name to contain the "
        "string 'dev' to make sure you don't mess up your production "
        "database. Are you sure you're using settings.development?")
    raise ImproperlyConfigured(error_message)

sys.stdout.write("Dropping current gridfs collection ...\n")
gridfs_storage._connection.drop_database(gridfs_storage.database)

sys.stdout.write("Adding files to gridfs collection and executing pipelines ...\n")

for doc in Document.objects.all():
    gridfs_storage.save(os.path.basename(doc.blob.name),
            "This is a test file with some test text.")
    create_pipeline({"_id": str(doc.blob.file._id), "id": doc.id})
