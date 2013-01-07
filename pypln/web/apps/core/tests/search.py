# coding: utf-8
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
import shutil

from django.core import management
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from mongodict import MongoDict

from core.models import Document
from core.tests.utils import (TestWithMongo, create_document,
                              create_corpus_and_documents,
                              update_documents_text_property)

__all__ = ["TestSearchPage"]


class TestSearchPage(TestWithMongo):
    fixtures = ['corpus']

    def setUp(self):
        super(TestSearchPage, self).setUp()

        self.search_url = reverse('search')
        try:
            shutil.rmtree(settings.INDEX_PATH)
        except OSError:
            pass

    def tearDown(self):
        super(TestSearchPage, self).tearDown()
        try:
            shutil.rmtree(settings.INDEX_PATH)
        except OSError:
            pass

    def test_requires_login(self):
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location', ''),
                         'http://testserver/account/login/?next=/search')

        self.client.login(username="admin", password="admin")
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)

    def test_management_command_update_index(self):
        create_corpus_and_documents(owner=self.user)

        management.call_command('update_index')
        # should not index since there is no 'text' for these documents
        for document in Document.objects.all():
            self.assertFalse(document.indexed)

        update_documents_text_property(store=self.store)
        management.call_command('update_index') # now will index
        for document in Document.objects.all():
            self.assertTrue(document.indexed)

    def test_search_should_work(self):
        corpus, doc_1, doc_2 = create_corpus_and_documents(owner=self.user)
        update_documents_text_property(store=self.store)
        management.call_command('update_index')

        self.client.login(username="admin", password="admin")
        response = self.client.get(self.search_url, data={'query': 'first'})
        self.assertTrue('results' in response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc_1)

        response = self.client.get(self.search_url, data={'query': 'second'})
        self.assertTrue('results' in response.context)
        results = response.context['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc_2)

        response = self.client.get(self.search_url, data={'query': 'test'})
        self.assertTrue('results' in response.context)
        results = response.context['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], doc_1)
        self.assertEqual(results[1], doc_2)

    def test_search_should_only_return_documents_owned_by_this_user(self):
        other_user = User(username="admin2", email='some@email.com',
                          password="admin2")
        other_user.set_password("admin2") #XXX: WTF, Pinax?
        other_user.save()
        corpus, doc_1, doc_2 = create_corpus_and_documents(owner=self.user)
        corpus, doc_3, doc_4 = create_corpus_and_documents(owner=other_user)
        update_documents_text_property(store=self.store)
        management.call_command('update_index')

        self.client.login(username="admin", password="admin")
        response = self.client.get(self.search_url, data={'query': 'first'})
        results = response.context['results']
        self.assertEqual(results[0], doc_1)
        response = self.client.get(self.search_url, data={'query': 'second'})
        results = response.context['results']
        self.assertEqual(results[0], doc_2)
        response = self.client.get(self.search_url, data={'query': 'test'})
        results = response.context['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], doc_1)
        self.assertEqual(results[1], doc_2)

        self.client.login(username="admin2", password="admin2")
        response = self.client.get(self.search_url, data={'query': 'first'})
        results = response.context['results']
        self.assertEqual(results[0], doc_3)
        response = self.client.get(self.search_url, data={'query': 'second'})
        results = response.context['results']
        self.assertEqual(results[0], doc_4)
        response = self.client.get(self.search_url, data={'query': 'test'})
        results = response.context['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], doc_3)
        self.assertEqual(results[1], doc_4)

    #TODO: test all breadcrumbs
