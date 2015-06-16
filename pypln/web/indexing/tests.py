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
# along with PyPLN.  If not, see <https://www.gnu.org/licenses/>.

from StringIO import StringIO

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from mock import patch
from rest_framework.reverse import reverse as rest_framework_reverse

from pypln.web.core.models import Corpus, IndexedDocument
from pypln.web.core.tests.utils import TestWithMongo


class IndexDocumentViewTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents']

    def setUp(self):
        self.user = User.objects.get(username="user")
        self.fp = StringIO("Content")
        self.fp.name = "document.txt"

    def test_requires_login(self):
        response = self.client.get(reverse('index-document'))
        self.assertEqual(response.status_code, 403)

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_create_new_document(self, create_indexing_pipelines):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp,
                "index_name": "test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(self.user.document_set.all()), 2)

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_cant_create_document_without_index_name(self, create_indexing_pipelines):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("index_name", response.data)
        self.assertEqual(len(self.user.document_set.all()), 1)

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_cant_create_document_without_doc_type(self, create_indexing_pipelines):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp,
                "index_name": "test_pypln"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("doc_type", response.data)
        self.assertEqual(len(self.user.document_set.all()), 1)

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_cant_create_document_for_another_user(self, create_indexing_pipeline):
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        corpus_url = rest_framework_reverse('corpus-detail', kwargs={'pk': corpus.id})
        data = {"corpus": corpus_url, "blob": self.fp, "owner": 1,
                "index_name": "test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 201)
        document = self.user.document_set.all()[1]
        self.assertEqual(document.owner, self.user)

    def test_cant_create_document_for_inexistent_corpus(self):
        self.client.login(username="user", password="user")

        corpus_url = rest_framework_reverse('corpus-detail', kwargs={'pk': 9999})
        data = {"corpus": corpus_url, "blob": self.fp,
                "index_name": "test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 400)

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_cant_create_document_in_another_users_corpus(self,
            create_indexing_pipeline):
        self.client.login(username="user", password="user")

        # We'll try to associate this document to a corpus that belongs to
        # 'admin'
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        corpus_url = rest_framework_reverse('corpus-detail',
                kwargs={'pk': corpus.id})
        data = {"corpus": corpus_url, "blob": self.fp,
                    "index_name": "test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 400)

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_creating_a_document_should_create_a_pipeline_for_it(self,
            create_indexing_pipeline):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp,
                "index_name": "test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(create_indexing_pipeline.called)
        doc_id = int(response.data['url'].split('/')[-2])
        document = IndexedDocument.objects.get(pk=doc_id)
        create_indexing_pipeline.assert_called_with(document)
