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
from cStringIO import StringIO
from bson import json_util
import mock
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from mongodict import MongoDict

from pypln.backend.mongodict_adapter import MongoDictAdapter
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

        filename = os.path.join(settings.PROJECT_ROOT, 'core/fixtures/mongodb/analysis.json')
        with open(filename, 'r') as mongo_fixture:
            for obj in json_util.loads(mongo_fixture.read()):
                gridfs_storage._connection[settings.MONGODB_CONFIG['database']].main.insert(obj)

        # `GridFSStorage.save()` uses `.get_available_name()` to get a
        # unique name from the filename we provide. In commit
        # dac93bdfd6c we changed the way it behaves to use the current
        # timestamp (the reasoning behind this is the commit message
        # for the original buggy commit: a5997bc94d). This means that
        # we cannot use the real behaviour to generate the filename we
        # get from our fixtures (since it will be appended with the
        # current timestamp), so here we briefly change the behaviour
        # of `.get_available_name()` to return the filename we gave
        # it, so we can create the correct files that are needed to
        # work with our fixtures. After the `with` block is over, the
        # behaviour of the method returns to normal.
        with mock.patch('pypln.web.core.models.gridfs_storage.get_available_name', new=lambda x: x):
            for doc in Document.objects.all():
                gridfs_storage.save(os.path.basename(doc.blob.name),
                                    StringIO("This is a test file."))

    def _post_teardown(self, *args, **kwargs):
        gridfs_storage._connection.drop_database(gridfs_storage.database)
        super(TestWithMongo, self)._post_teardown(*args, **kwargs)
