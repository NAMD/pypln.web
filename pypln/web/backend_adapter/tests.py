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

from django.conf import settings
from django.test import TestCase
from mock import patch

from pypln.web.backend_adapter.pipelines import create_pipeline
from pypln.backend.mongodict_adapter import MongoDictAdapter

__all__ = ["CreatePipelineTest"]

class CreatePipelineTest(TestWithMongo):

    @patch('pypln.web.backend_adapter.pipelines.GridFSDataRetriever', autospec=True)
    def test_should_create_pipelines_for_document(self, gridfs_data_retriever):
        pipeline_data = {"_id": "123", "id": 1}
        create_pipeline(pipeline_data)
        gridfs_data_retriever.assert_called_with()
        gridfs_data_retriever.return_value.si.assert_called_with(1)

    @patch('pypln.web.backend_adapter.pipelines.GridFSDataRetriever', autospec=True)
    def test_should_add_file_id_to_the_document_in_mongo(self,
            gridfs_data_retriever):
        pipeline_data = {"_id": "123", "id": 1}
        create_pipeline(pipeline_data)
        document = MongoDictAdapter(doc_id=pipeline_data['id'],
                host=settings.MONGODB_CONFIG['host'],
                port=settings.MONGODB_CONFIG['port'],
                database=settings.MONGODB_CONFIG['database'])
        self.assertEqual(document['file_id'], pipeline_data['_id'])
