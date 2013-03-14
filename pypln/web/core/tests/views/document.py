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
from mock import patch
from StringIO import StringIO

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT
from rest_framework.reverse import reverse as rest_framework_reverse

from pypln.web.core.models import Corpus, Document
from pypln.web.core.tests.utils import TestWithMongo

__all__ = ["DocumentListViewTest", "DocumentDetailViewTest"]


class DocumentListViewTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents']

    def setUp(self):
        self.user = User.objects.get(username="user")
        self.fp = StringIO("Content")
        self.fp.name = "document.txt"

    def test_requires_login(self):
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 403)

    def test_only_lists_documents_that_belong_to_the_authenticated_user(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('document-list'))
        self.assertEqual(response.status_code, 200)

        expected_data = Document.objects.filter(
                owner=User.objects.get(username="user"))
        object_list = response.renderer_context['view'].object_list

        self.assertEqual(list(expected_data), list(object_list))

    @patch('pypln.web.core.views.create_pipeline')
    def test_create_new_document(self, create_pipelines):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp}
        response = self.client.post(reverse('document-list'), data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(self.user.document_set.all()), 2)

    @patch('pypln.web.core.views.create_pipeline')
    def test_cant_create_document_for_another_user(self, create_pipeline):
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        corpus_url = rest_framework_reverse('corpus-detail', kwargs={'pk': corpus.id})
        data = {"corpus": corpus_url, "blob": self.fp, "owner": 1}
        response = self.client.post(reverse('document-list'), data)

        self.assertEqual(response.status_code, 201)
        document = self.user.document_set.all()[1]
        self.assertEqual(document.owner, self.user)

    def test_cant_create_document_for_inexistent_corpus(self):
        self.client.login(username="user", password="user")

        corpus_url = rest_framework_reverse('corpus-detail', kwargs={'pk': 9999})
        data = {"corpus": corpus_url, "blob": self.fp}
        response = self.client.post(reverse('document-list'), data)

        self.assertEqual(response.status_code, 400)

    @patch('pypln.web.core.views.create_pipeline')
    def test_cant_create_document_in_another_users_corpus(self, create_pipelines):
        self.client.login(username="user", password="user")

        # We'll try to associate this document to a corpus that belongs to
        # 'admin'
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        corpus_url = rest_framework_reverse('corpus-detail', kwargs={'pk': corpus.id})
        data = {"corpus": corpus_url, "blob": self.fp}
        response = self.client.post(reverse('document-list'), data)

        self.assertEqual(response.status_code, 400)

    @patch('pypln.web.core.views.create_pipeline')
    def test_creating_a_document_should_create_a_pipeline_for_it(self, create_pipeline):
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        data = {"corpus": rest_framework_reverse('corpus-detail',
            kwargs={'pk': corpus.id}), "blob": self.fp}
        response = self.client.post(reverse('document-list'), data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(create_pipeline.called)
        document = response.renderer_context['view'].object
        pipeline_data = {"_id": str(document.blob.file._id), "id": document.id}
        create_pipeline.assert_called_with(pipeline_data)


class DocumentDetailViewTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents']

    def setUp(self):
        self.user = User.objects.get(username="user")
        self.fp = StringIO("Content")
        self.fp.name = "document.txt"

    def _get_corpus_url(self, corpus_id):
        return rest_framework_reverse('corpus-detail',
                kwargs={'pk': corpus_id})

    def test_requires_login(self):
        document = Document.objects.filter(owner__username='user')[0]
        response = self.client.get(reverse('document-detail',
            kwargs={'pk': document.id}))
        self.assertEqual(response.status_code, 403)

    def test_shows_document_correctly(self):
        self.client.login(username="user", password="user")
        document = Document.objects.filter(owner__username="user")[0]
        response = self.client.get(reverse('document-detail',
            kwargs={'pk': document.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.renderer_context['view'].object, document)

    def test_returns_404_for_inexistent_document(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('document-detail',
            kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_user_is_not_the_owner_of_the_document(self):
        self.client.login(username="user", password="user")
        document = Document.objects.filter(owner__username="admin")[0]
        response = self.client.get(reverse('document-detail',
            kwargs={'pk': document.id}))
        self.assertEqual(response.status_code, 404)

    def test_edit_document(self):
        self.client.login(username="user", password="user")

        document = self.user.document_set.all()[0]
        new_corpus = Corpus.objects.create(name="New corpus",
                description="", owner=self.user)
        data = encode_multipart(BOUNDARY, {"corpus": self._get_corpus_url(
            new_corpus.id), "blob": self.fp})
        response = self.client.put(reverse('document-detail',
            kwargs={'pk': document.id}), data, content_type=MULTIPART_CONTENT)

        self.assertEqual(response.status_code, 200)
        updated_document = Document.objects.get(id=document.id)
        self.assertEqual(updated_document.corpus, new_corpus)

    def test_cant_edit_other_peoples_documents(self):
        self.client.login(username="user", password="user")
        document = Document.objects.filter(owner__username="admin")[0]
        data = encode_multipart(BOUNDARY,
                {"corpus": self._get_corpus_url(document.corpus.id),
                    "blob": self.fp})
        response = self.client.put(reverse('document-detail',
            kwargs={'pk': document.id}), data, content_type=MULTIPART_CONTENT)

        self.assertEqual(response.status_code, 400)

    def test_cant_change_the_owner_of_a_document(self):
        self.client.login(username="user", password="user")
        document = self.user.document_set.all()[0]
        # We try to set 'admin' as the owner (id=1)
        data = encode_multipart(BOUNDARY, {"blob": self.fp,
            "corpus": self._get_corpus_url(document.corpus.id), "owner": 1})

        response = self.client.put(reverse('document-detail',
            kwargs={'pk': document.id}), data, content_type=MULTIPART_CONTENT)

        self.assertEqual(response.status_code, 200)
        # but the view sets the request user as the owner anyway
        self.assertEqual(response.data["owner"], "user")

    def test_delete_a_document(self):
        self.client.login(username="user", password="user")
        self.assertEqual(len(self.user.document_set.all()), 1)

        document = self.user.document_set.all()[0]
        response = self.client.delete(reverse('document-detail',
            kwargs={'pk': document.id}))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(self.user.document_set.all()), 0)

    def test_cant_delete_other_peoples_documents(self):
        self.client.login(username="user", password="user")
        self.assertEqual(len(Corpus.objects.filter(owner__username="admin")), 1)

        document = Document.objects.filter(owner__username="admin")[0]
        response = self.client.delete(reverse('document-detail',
            kwargs={'pk': document.id}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Corpus.objects.filter(owner__username="admin")), 1)
