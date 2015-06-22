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

import elasticsearch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from mock import patch
from rest_framework.reverse import reverse as rest_framework_reverse

from pypln.web.core.models import Corpus, IndexedDocument
from pypln.web.core.tests.utils import TestWithMongo

SAMPLE_TEXT = """
Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, `and what is the use of a book,' thought Alice `without pictures or conversation?'

So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy- chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.

There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, `Oh dear! Oh dear! I shall be late!' (when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural); but when the Rabbit actually took a watch out of its waistcoat- pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.

In another moment down went Alice after it, never once considering how in the world she was to get out again.
"""


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
    def test_index_name_should_be_prefixed_with_username_if_its_not_already(self, create_indexing_pipelines):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp,
                "index_name": "test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 201)
        doc_id = int(response.data['url'].rsplit('/')[-2])
        created_document = IndexedDocument.objects.get(pk=doc_id)
        self.assertEqual(created_document.index_name, "user_test_pypln")

    @patch('pypln.web.indexing.views.create_indexing_pipeline')
    def test_index_name_that_start_with_username_dont_need_prefix(self, create_indexing_pipelines):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp,
                "index_name": "user_test_pypln", "doc_type": "article"}
        response = self.client.post(reverse('index-document'), data)

        self.assertEqual(response.status_code, 201)
        doc_id = int(response.data['url'].rsplit('/')[-2])
        created_document = IndexedDocument.objects.get(pk=doc_id)
        self.assertEqual(created_document.index_name, "user_test_pypln")

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

class IndexQueryViewTest(TestWithMongo):
    fixtures = ['users', ]#'corpora', 'documents']
    ES = elasticsearch.Elasticsearch(hosts=settings.ELASTICSEARCH_CONFIG['hosts'])

    def setUp(self):
        self.user = User.objects.get(username="user")
        self.fp = StringIO("Content")
        self.fp.name = "document.txt"

        self.index_name = "user_test_pypln"

        self.ES.indices.create(self.index_name)
        # `refresh=True` makes sure the index is updated when we search it
        self.ES.index(index=self.index_name, doc_type="article",
                body={"text": SAMPLE_TEXT}, id="1234", refresh=True)

    def tearDown(self):
        self.ES.indices.delete(index=self.index_name)

    def test_requires_login(self):
        response = self.client.get(reverse('index-query'))
        self.assertEqual(response.status_code, 403)

    def test_POST_is_not_allowed(self):
        self.client.login(username="user", password="user")
        response = self.client.post(reverse('index-query'))
        self.assertEqual(response.status_code, 405)

    def test_needs_index_name(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('index-query'),
                {"q": "Alice"})
        self.assertEqual(response.status_code, 400)

    def test_needs_query(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('index-query'),
                {"index_name": self.index_name})
        self.assertEqual(response.status_code, 400)

    def test_successfull_query(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('index-query'),
                {"index_name": self.index_name, "q": "Alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["hits"]), 1)
        hit = response.data["hits"][0]
        self.assertEqual(hit["_index"], self.index_name)
        self.assertEqual(hit["_id"], "1234")
        self.assertEqual(hit["_type"], "article")
        self.assertEqual(hit["_source"]["text"], SAMPLE_TEXT)

    def test_query_with_no_results(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('index-query'),
                {"index_name": self.index_name, "q": "Inexistentword"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["hits"]), 0)

    def test_only_finds_items_from_the_requested_index(self):
        new_index_name = "{}_{}".format(self.index_name, 2)

        # Create a new index with a different name
        self.ES.indices.create(new_index_name)
        self.ES.index(index=new_index_name, doc_type="article",
                body={"text": SAMPLE_TEXT}, id="1234", refresh=True)

        self.client.login(username="user", password="user")
        # Query the original index
        response = self.client.get(reverse('index-query'),
                {"index_name": self.index_name, "q": "Alice"})
        self.assertEqual(response.status_code, 200)

        try:
            for hit in response.data["hits"]:
                self.assertEqual(hit["_index"], self.index_name)
        finally:
            # Make sure we delete the newly created index
            self.ES.indices.delete(index=new_index_name)

    def test_query_inexistent_index(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('index-query'),
                {"index_name": 'user_inexistent_index_for_pypln_test',
                 "q": "Alice"})
        self.assertEqual(response.status_code, 404)

    def test_querying_another_users_index_should_not_be_possible(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('index-query'),
                {"index_name": 'admin_test_pypln',
                 "q": "Alice"})
        self.assertEqual(response.status_code, 400)
