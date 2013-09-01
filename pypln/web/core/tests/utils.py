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
import json
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from mongodict import MongoDict

from pypln.web.core.models import Document, gridfs_storage

class TestWithMongo(TestCase):

    def _pre_setup(self, *args, **kwargs):
        super(TestWithMongo, self)._pre_setup(*args, **kwargs)
        if 'test' not in gridfs_storage.database:
            error_message = ("We expect the mongodb database name to contain the "
                "string 'test' to make sure you don't mess up your production "
                "database. Are you sure you're using settings.test to run these "
                "tests?")
            raise ImproperlyConfigured(error_message)

        gridfs_storage._connection.drop_database(gridfs_storage.database)

        for doc in Document.objects.all():
            gridfs_storage.save(os.path.basename(doc.blob.name),
                    "This is a test file with some test text.")

        self.store = MongoDict(host=settings.MONGODB_CONFIG['host'],
               port=settings.MONGODB_CONFIG['port'],
               database=settings.MONGODB_CONFIG['database'],
               collection=settings.MONGODB_CONFIG['analysis_collection'])

        filename = os.path.join(settings.PROJECT_ROOT, 'core/fixtures/mongodb/analysis.json')
        with open(filename, 'r') as mongo_fixture:
            for obj in json.load(mongo_fixture):
                self.store[obj['_id']] = obj['value']

    def _post_teardown(self, *args, **kwargs):
        gridfs_storage._connection.drop_database(gridfs_storage.database)
        super(TestWithMongo, self)._post_teardown(*args, **kwargs)
