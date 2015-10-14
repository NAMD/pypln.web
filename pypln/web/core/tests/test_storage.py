# -*- coding:utf-8 -*-
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
from mock import MagicMock
from django.core.files.base import ContentFile
from django.test import TestCase

from pypln.web.core.storage import MongoDBBase64Storage


class MongoDBBase64StorageTest(TestCase):
    def test_saving_file_returns_document_id_as_filename(self):
        content = 'This is the file content with non-ascii chars: á.'
        storage = MongoDBBase64Storage()
        storage.collection.insert = MagicMock(return_value='mocked_id')
        file_obj = ContentFile(content)
        name = storage.save('filename.txt', content=file_obj)
        self.assertEqual('mocked_id', name)

    def test_saving_file_stores_base64_encoded_data(self):
        content = 'This is the file content with non-ascii chars: á.'
        base64_encoded_content = base64.b64encode(content)
        storage = MongoDBBase64Storage()
        file_obj = ContentFile(content)
        name = storage.save('filename.txt', content=file_obj)
        saved_file = storage.collection.find_one({'_id': ObjectId(name)})
        self.assertEqual(saved_file['contents'], base64_encoded_content)

    def test_opening_file_returns_file_object_with_original_data(self):
        content = 'This is the file content with non-ascii chars: á.'
        base64_encoded_content = base64.b64encode(content)
        storage = MongoDBBase64Storage()
        file_obj = ContentFile(content)
        _id = storage.collection.insert(
                {'contents': base64_encoded_content})
        self.assertEqual(storage.open(str(_id)).read(), content)

    def test_retrieving_data_for_file_that_does_not_exist(self):
        content = 'This is the file content with non-ascii chars: á.'
        base64_encoded_content = base64.b64encode(content)
        storage = MongoDBBase64Storage()
        file_obj = ContentFile(content)
        _id = storage.collection.insert(
                {'contents': base64_encoded_content})
        with self.assertRaises(ValueError):
            storage.open(ObjectId('abcdabcd1234567812345678'))

