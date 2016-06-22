# coding: utf-8
#
# Copyright 2015 NAMD-EMAP-FGV
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

import base64
from bson import ObjectId
import os
import time
import urlparse
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.encoding import filepath_to_uri
from pymongo import Connection


class MongoDBBase64Storage(Storage):
    """
    This storage saves the file content as a base64 encoded string in MongoDB.
    We're not using GridFS because the workers will need the base64 encoded
    data anyways, and we also have a small file size limit that should make
    sure the MongoDB document does not exceed the maximum document size.
    """

    def __init__(self):

        self._connection = Connection(host=settings.MONGODB_URIS)
        self._db = self._connection[settings.MONGODB_DBNAME]
        self.collection = self._db[settings.MONGODB_COLLECTION]

    def _open(self, name, mode='rb'):
        document = self.collection.find_one(ObjectId(name))
        if document is None:
            raise ValueError("Document with name {} does not exist".format(name))
        content = base64.b64decode(document['contents'])
        return ContentFile(content)

    def _save(self, name, content):
        content.seek(0)
        encoded_content = base64.b64encode(content.read())
        _id = self.collection.insert({'contents': encoded_content})
        return str(_id)

    def get_available_name(self, name, max_length=None):
        return "fake_name"

    def size(self, path):
        document = self.collection.find_one({'_id': ObjectId(path)})
        # when we b64decode 'contents' we get a str (not a unicode obj) so we
        # can just get it's len() and have it's size.
        return len(base64.b64decode(document['contents']))

    def __del__(self):
        self._connection.close()
