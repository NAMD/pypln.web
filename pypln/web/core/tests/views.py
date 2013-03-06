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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from pypln.web.core.models import Corpus, Document

__all__ = ["CorpusListViewTest", "CorpusDetailViewTest",
    "DocumentListViewTest", "DocumentDetailViewTest"]

class CorpusListViewTest(TestCase):
    fixtures = ['corpora']

    def test_requires_login(self):
        response = self.client.get(reverse('corpus-list'))
        self.assertEqual(response.status_code, 403)

    def test_only_lists_corpora_that_belongs_to_the_authenticated_user(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('corpus-list'))
        self.assertEqual(response.status_code, 200)

        expected_data = Corpus.objects.filter(
                owner=User.objects.get(username="user"))
        object_list = response.renderer_context['view'].object_list

        self.assertEqual(list(expected_data), list(object_list))

    def test_create_new_corpus(self):
        user = User.objects.get(username="user")
        self.assertEqual(len(user.corpus_set.all()), 1)
        self.client.login(username="user", password="user")
        response = self.client.post(reverse('corpus-list'), {"name": "Corpus",
            "description": "description"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(user.corpus_set.all()), 2)

    def test_cant_create_new_corpus_for_another_user(self):
        self.client.login(username="user", password="user")
        # We try to set 'admin' as the owner (id=1)
        response = self.client.post(reverse('corpus-list'), {"name": "Corpus",
            "description": "description", "owner": 1})
        self.assertEqual(response.status_code, 201)
        # but the view sets the request user as the owner anyway
        self.assertEqual(response.data["owner"], "user")

class CorpusDetailViewTest(TestCase):
    fixtures = ['corpora']

    def test_requires_login(self):
        response = self.client.get(reverse('corpus-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 403)

    def test_shows_corpus_correctly(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="user")[0]
        response = self.client.get(reverse('corpus-detail',
            kwargs={'pk': corpus.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.renderer_context['view'].object, corpus)

    def test_returns_404_for_inexistent_corpus(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('corpus-detail',
            kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_returns_403_if_user_is_not_the_owner_of_the_corpus(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.get(reverse('corpus-detail',
            kwargs={'pk': corpus.id}))
        self.assertEqual(response.status_code, 403)

    def test_edit_corpus(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="user")[0]
        response = self.client.put(reverse('corpus-detail',
            kwargs={'pk': corpus.id}), json.dumps({"name": "New name",
            "description": "New description"}), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        updated_corpus = Corpus.objects.filter(owner__username="user")[0]
        self.assertEqual(updated_corpus.name, "New name")
        self.assertEqual(updated_corpus.description, "New description")

    def test_cant_edit_other_peoples_corpora(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.put(reverse('corpus-detail',
            kwargs={'pk': corpus.id}), json.dumps({"name": "New name",
            "description": "New description"}), content_type="application/json")

        self.assertEqual(response.status_code, 403)

    def test_cant_change_the_owner_of_a_corpus(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="user")[0]
        # We try to set 'admin' as the owner (id=1)
        response = self.client.put(reverse('corpus-detail',
            kwargs={'pk': corpus.id}), json.dumps({"name": "Corpus",
            "description": "description", "owner": 1}),
            content_type="application/json")

        self.assertEqual(response.status_code, 200)
        # but the view sets the request user as the owner anyway
        self.assertEqual(response.data["owner"], "user")

    def test_delete_a_corpus(self):
        self.client.login(username="user", password="user")
        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)

        corpus = Corpus.objects.filter(owner__username="user")[0]
        response = self.client.delete(reverse('corpus-detail',
            kwargs={'pk': corpus.id}))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 0)

    def test_cant_delete_other_peoples_corpora(self):
        self.client.login(username="user", password="user")
        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)

        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.delete(reverse('corpus-detail',
            kwargs={'pk': corpus.id}))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)


class DocumentListViewTest(TestCase):
    fixtures = ['corpora', 'documents']

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


class DocumentDetailViewTest(TestCase):
    fixtures = ['corpora', 'documents']

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

    def test_returns_403_if_user_is_not_the_owner_of_the_document(self):
        self.client.login(username="user", password="user")
        document = Document.objects.filter(owner__username="admin")[0]
        response = self.client.get(reverse('document-detail',
            kwargs={'pk': document.id}))
        self.assertEqual(response.status_code, 403)
