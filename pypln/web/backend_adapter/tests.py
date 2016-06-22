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
from StringIO import StringIO

from bson import ObjectId
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from mock import patch

from pypln.web.backend_adapter.pipelines import (create_indexing_pipeline,
        call_default_pipeline, create_pipeline_from_document)
from pypln.web.core.models import IndexedDocument, Document, mongodb_storage
from pypln.web.core.tests.utils import TestWithMongo


__all__ = ["CreatePipelineTest", "CreateIndexingPipelineTest",
    "CreatePipelineFromDocumentTest"]

class CreatePipelineTest(TestWithMongo):

    @patch('pypln.web.backend_adapter.pipelines.Extractor', autospec=True)
    def test_should_create_pipelines_for_document(self, extractor):
        _id = ObjectId("123456789012")
        call_default_pipeline(_id)
        extractor.assert_called_with()
        extractor.return_value.si.assert_called_with(_id)


class CreateIndexingPipelineTest(TestWithMongo):
    fixtures = ["users", "corpora"]

    def setUp(self):
        user = User.objects.get(id=1)
        self.document = IndexedDocument.objects.create(
            owner=user,
            blob=File(StringIO('test content.'), 'test_file.txt'),
            corpus=user.corpus_set.all()[0],
            doc_type="article",
            index_name="test_pypln",
        )


    def get_mongo_doc(self, doc):
        return mongodb_storage.collection.find_one({"_id":
            ObjectId(doc.blob.name)})

    @patch('pypln.web.backend_adapter.pipelines.Extractor', autospec=True)
    def test_should_create_indexing_pipelines_for_document(self, extractor):
        create_indexing_pipeline(self.document)
        extractor.assert_called_with()
        extractor.return_value.si.assert_called_with(ObjectId(self.document.blob.name))

    @patch('pypln.web.backend_adapter.pipelines.Extractor', autospec=True)
    def test_should_add_index_name_to_the_document_in_mongo(self,
            gridfs_data_retriever):
        create_indexing_pipeline(self.document)
        mongo_document = self.get_mongo_doc(self.document)
        self.assertEqual(mongo_document['index_name'], self.document.index_name)

    @patch('pypln.web.backend_adapter.pipelines.Extractor', autospec=True)
    def test_should_add_doc_type_to_the_document_in_mongo(self,
            gridfs_data_retriever):
        create_indexing_pipeline(self.document)
        mongo_document = self.get_mongo_doc(self.document)
        self.assertEqual(mongo_document['doc_type'], self.document.doc_type)


class CreatePipelineFromDocumentTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents']

    @patch('pypln.web.backend_adapter.pipelines.call_default_pipeline', autospec=True)
    def test_create_pipeline_from_document_instantiates_a_document_id(self, fake_call_default_pipeline):
        doc = Document.objects.all()[0]
        create_pipeline_from_document(doc)
        fake_call_default_pipeline.assert_called_with(ObjectId(doc.blob.name))
