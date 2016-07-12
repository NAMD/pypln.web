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

from pypln.web.core.models import Document, mongodb_storage

class TestWithMongo(TestCase):

    def _pre_setup(self, *args, **kwargs):
        super(TestWithMongo, self)._pre_setup(*args, **kwargs)
        mongodb_storage._connection.drop_database(mongodb_storage._db.name)

        if hasattr(self, 'fixtures') and self.fixtures is not None and 'documents' in self.fixtures:
            filename = os.path.join(settings.PROJECT_ROOT, 'core/fixtures/mongodb/analysis.json')
            with open(filename, 'r') as mongo_fixture:
                for obj in json_util.loads(mongo_fixture.read()):
                    mongodb_storage._connection[settings.MONGODB_DBNAME][settings.MONGODB_COLLECTION].insert(obj)
            for doc in Document.objects.all():
                mongodb_storage.save(os.path.basename(doc.blob.name),
                    StringIO(u"Test file with non-ascii char: á.".encode('utf-8')))

        if hasattr(self, 'fixtures') and self.fixtures is not None and 'corpora_analysis' in self.fixtures:
            filename = os.path.join(settings.PROJECT_ROOT, 'core/fixtures/mongodb/corpora_analysis.json')
            with open(filename, 'r') as mongo_fixture:
                for obj in json_util.loads(mongo_fixture.read()):
                    mongodb_storage._connection[settings.MONGODB_DBNAME][settings.MONGODB_CORPORA_COLLECTION].insert(obj, w=1)


    def _post_teardown(self, *args, **kwargs):
        mongodb_storage._connection.drop_database(mongodb_storage._db.name)
        super(TestWithMongo, self)._post_teardown(*args, **kwargs)
