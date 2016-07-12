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
from mock import patch

from pypln.web.core.models import Corpus, User
from pypln.web.core.tests.utils import TestWithMongo

__all__ = ["CorpusFreqDistViewTest"]


class CorpusFreqDistViewTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents', 'corpora_analysis']

    def test_requires_login(self):
        response = self.client.get(reverse('corpus-freqdist',
            kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 403)

    def test_returns_404_for_inexistent_corpus(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('corpus-freqdist',
            kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_user_is_not_the_owner_of_the_corpus(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.get(reverse('corpus-freqdist',
            kwargs={'pk': corpus.id}))
        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_corpus_has_no_freqdist_yet(self):
        self.client.login(username="admin", password="admin")
        corpus = Corpus.objects.filter(owner__username="admin")[0]
        response = self.client.get(reverse('corpus-freqdist',
            kwargs={'pk': corpus.id}))
        self.assertEqual(response.status_code, 404)

    def test_shows_corpus_freqdist_correctly(self):
        self.client.login(username="user", password="user")
        corpus = Corpus.objects.filter(owner__username="user")[0]
        response = self.client.get(reverse('corpus-freqdist',
            kwargs={'pk': corpus.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.renderer_context['view'].get_object(),
                         corpus)
        expected_data = corpus.properties['freqdist']
        self.assertEqual(response.data['value'], expected_data)


    @patch('pypln.web.backend_adapter.pipelines.corpus_freqdist')
    def _test_queue_freqdist_analysis_for_a_corpus_that_didnt_have_one(self,
            corpus_freqdist):
        self.user = User.objects.get(username="user")
        self.assertEqual(len(self.user.document_set.all()), 1)
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        response = self.client.put(reverse('corpus-freqdist',
            kwargs={"pk": corpus.id}))

        self.assertEqual(response.status_code, 201)
        self.assertTrue(corpus_freqdist.called)

        document_ids = corpus.document_set.all()

        corpus_freqdist.assert_called_with(corpus.id, document_ids)

#    def test_edit_corpus(self):
#        self.client.login(username="user", password="user")
#        corpus = Corpus.objects.filter(owner__username="user")[0]
#        response = self.client.put(reverse('corpus-detail',
#            kwargs={'pk': corpus.id}), json.dumps({"name": "New name",
#            "description": "New description"}), content_type="application/json")
#
#        self.assertEqual(response.status_code, 200)
#        updated_corpus = Corpus.objects.filter(owner__username="user")[0]
#        self.assertEqual(updated_corpus.name, "New name")
#        self.assertEqual(updated_corpus.description, "New description")
#
#    def test_cant_change_name_to_one_that_already_exists_for_this_user(self):
#        self.client.login(username="user", password="user")
#        user = User.objects.get(username="user")
#        conflicting_corpus = Corpus.objects.create(name="Conflicting name",
#                owner=user, description="This corpus is here to create a conflict")
#
#        corpus = Corpus.objects.filter(owner__username="user")[0]
#        response = self.client.put(reverse('corpus-detail',
#            kwargs={'pk': corpus.id}), json.dumps({"name": "Conflicting name",
#            "description": "New description"}), content_type="application/json")
#
#        self.assertEqual(response.status_code, 400)
#        not_updated_corpus = Corpus.objects.filter(owner__username="user")[0]
#        self.assertEqual(not_updated_corpus.name, "User Test Corpus")
#        self.assertEqual(not_updated_corpus.description, "This corpus belongs to the user 'user'")
#
#    def test_cant_edit_other_peoples_corpora(self):
#        """
#        A PUT request to another person's corpus actually raises Http404, as
#        if the document did not exist. Since rest_framework uses PUT-as-create,
#        this means a new object is created with the provided information.
#        """
#        self.client.login(username="user", password="user")
#        corpus = Corpus.objects.filter(owner__username="admin")[0]
#        response = self.client.put(reverse('corpus-detail',
#            kwargs={'pk': corpus.id}), json.dumps({"name": "New name",
#            "description": "New description"}), content_type="application/json")
#        self.assertEqual(response.status_code, 404)
#
#        reloaded_corpus = Corpus.objects.filter(owner__username="admin")[0]
#        self.assertNotEqual(reloaded_corpus.name, "New name")
#        self.assertNotEqual(reloaded_corpus.description, "New description")
#
#    def test_cant_change_the_owner_of_a_corpus(self):
#        self.client.login(username="user", password="user")
#        corpus = Corpus.objects.filter(owner__username="user")[0]
#        # We try to set 'admin' as the owner (id=1)
#        response = self.client.put(reverse('corpus-detail',
#            kwargs={'pk': corpus.id}), json.dumps({"name": "Corpus",
#            "description": "description", "owner": 1}),
#            content_type="application/json")
#
#        self.assertEqual(response.status_code, 200)
#        # but the view sets the request user as the owner anyway
#        self.assertEqual(response.data["owner"], "user")
#
#    def test_delete_a_corpus(self):
#        self.client.login(username="user", password="user")
#        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)
#
#        corpus = Corpus.objects.filter(owner__username="user")[0]
#        response = self.client.delete(reverse('corpus-detail',
#            kwargs={'pk': corpus.id}))
#
#        self.assertEqual(response.status_code, 204)
#        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 0)
#
#    def test_cant_delete_other_peoples_corpora(self):
#        self.client.login(username="user", password="user")
#        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)
#
#        corpus = Corpus.objects.filter(owner__username="admin")[0]
#        response = self.client.delete(reverse('corpus-detail',
#            kwargs={'pk': corpus.id}))
#
#        self.assertEqual(response.status_code, 404)
#        self.assertEqual(len(Corpus.objects.filter(owner__username="user")), 1)
#"""
