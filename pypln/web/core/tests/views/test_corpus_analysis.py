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

    @patch('pypln.web.core.views.corpus_freqdist')
    def test_queue_freqdist_analysis_for_a_corpus_that_still_does_not_have_one(self,corpus_freqdist):
        """
        This is a regression test. There used to be a bug that returned 404
        before queueing the analysis if the corpus didn't have a freqdist
        analysis yet.
        """
        self.user = User.objects.get(username="admin")
        self.client.login(username="admin", password="admin")

        corpus = self.user.corpus_set.all()[0]
        response = self.client.put(reverse('corpus-freqdist',
            kwargs={"pk": corpus.id}))

        self.assertFalse(corpus.properties.has_key("freqdist"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(corpus_freqdist.called)
        corpus_freqdist.assert_called_with(corpus)

    @patch('pypln.web.core.views.corpus_freqdist')
    def test_queue_freqdist_analysis_for_a_corpus_that_has_one(self,corpus_freqdist):
        self.user = User.objects.get(username="user")
        self.client.login(username="user", password="user")

        corpus = self.user.corpus_set.all()[0]
        response = self.client.put(reverse('corpus-freqdist',
            kwargs={"pk": corpus.id}))

        self.assertTrue(corpus.properties.has_key("freqdist"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(corpus_freqdist.called)
        corpus_freqdist.assert_called_with(corpus)
