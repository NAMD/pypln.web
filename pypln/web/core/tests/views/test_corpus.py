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

from pypln.web.core.models import Corpus

__all__ = ["CorpusListViewTest", "CorpusDetailViewTest"]


class CorpusListViewTest(TestCase):
    fixtures = ['users', 'corpora']

    def test_requires_login(self):
        response = self.client.get(reverse('corpus-list'))
        self.assertEqual(response.status_code, 403)

    def test_only_lists_corpora_that_belongs_to_the_authenticated_user(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('corpus-list'))
        self.assertEqual(response.status_code, 200)

        expected_data = Corpus.objects.filter(
                owner=User.objects.get(username="user"))
        object_list = response.renderer_context['view'].get_queryset()

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

    def test_cant_create_duplicate_corpus(self):
        user = User.objects.get(username="user")
        self.assertEqual(len(user.corpus_set.all()), 1)
        self.client.login(username="user", password="user")

        # A corpus with this information already exists (loaded by fixtures)
        response = self.client.post(reverse('corpus-list'), {"name": "User Test Corpus",
            "description": "description"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(user.corpus_set.all()), 1)


class CorpusDetailViewTest(TestCase):
    fixtures = ['users', 'corpora']

    def test_requires_login(self):
        response = self.client.get(reverse('corpus-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 403)

    def test_shows_corpus_correctly(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="user")[0]
        response = self.client.get(reverse('corpus-detail',
            kwargs={'pk': corpus.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.renderer_context['view'].get_object(), corpus)

    def test_returns_404_for_inexistent_corpus(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('corpus-detail',
            kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_user_is_not_the_owner_of_the_corpus(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.get(reverse('corpus-detail',
            kwargs={'pk': corpus.id}))
        self.assertEqual(response.status_code, 404)

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

    def test_cant_change_name_to_one_that_already_exists_for_this_user(self):
        self.client.login(username="user", password="user")
        user = User.objects.get(username="user")
        conflicting_corpus = Corpus.objects.create(name="Conflicting name",
                owner=user, description="This corpus is here to create a conflict")

        corpus = Corpus.objects.filter(owner__username="user")[0]
        response = self.client.put(reverse('corpus-detail',
            kwargs={'pk': corpus.id}), json.dumps({"name": "Conflicting name",
            "description": "New description"}), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        not_updated_corpus = Corpus.objects.filter(owner__username="user")[0]
        self.assertEqual(not_updated_corpus.name, "User Test Corpus")
        self.assertEqual(not_updated_corpus.description, "This corpus belongs to the user 'user'")

    def test_cant_edit_other_peoples_corpora(self):
        """
        A PUT request to another person's corpus actually raises Http404, as
        if the document did not exist. Since rest_framework uses PUT-as-create,
        this means a new object is created with the provided information.
        """
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.put(reverse('corpus-detail',
            kwargs={'pk': corpus.id}), json.dumps({"name": "New name",
            "description": "New description"}), content_type="application/json")
        self.assertEqual(response.status_code, 404)

        reloaded_corpus = Corpus.objects.filter(owner__username="admin")[0]
        self.assertNotEqual(reloaded_corpus.name, "New name")
        self.assertNotEqual(reloaded_corpus.description, "New description")

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

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)
