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

from StringIO import StringIO
from datetime import datetime
from mock import patch
import shutil

import pymongo

from datetime import datetime
from StringIO import StringIO

from django.core import management
from django.core.files import File
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.conf import settings

from django.contrib.auth.models import User

from django.test.client import Client
from mongodict import MongoDict

from core.models import gridfs_storage, Corpus, Document, index_schema
from core.forms import DocumentForm
from core import views

from views import *
from forms import *
from models import *

def _create_document(filename, contents, owner):
    fp = StringIO()
    fp.write(contents)
    fp.seek(0)
    fp.name = filename
    fp.size = len(contents.encode('utf-8')) # seriously, Django?

    document = Document(slug=filename, owner=owner,
            date_uploaded=datetime.now(), indexed=False)
    document.blob.save(filename, File(fp))
    document.save()
    return document

def _create_corpus_and_documents(owner):
    document_1_text = u'this is the first test.\n'
    document_2_text = u'this is the second test.\n'
    document_1 = _create_document(filename='/doc-1.txt', owner=owner,
            contents=document_1_text)
    document_2 = _create_document(filename='/doc-2.txt', owner=owner,
            contents=document_2_text)

    now = datetime.now()
    corpus = Corpus(name='Test', slug='test', owner=owner,
            date_created=now, last_modified=now)
    corpus.save()
    corpus.documents.add(document_1)
    corpus.documents.add(document_2)
    corpus.save()

    return corpus, document_1, document_2

def _update_documents_text_property(store):
    for document in Document.objects.all():
        text = document.blob.read()
        store['id:{}:text'.format(document.id)] = text
        store['id:{}:_properties'.format(document.id)] = ['text']

class TestSearchPage(TestCase):
    fixtures = ['corpus']

    def setUp(self):
        if 'test' not in gridfs_storage.database:
            error_message = ("We expect the mongodb database name to contain the "
                "string 'test' to make sure you don't mess up your production "
                "database. Are you sure you're using settings.test to run these "
                "tests?")
            raise ImproperlyConfigured(error_message)

        gridfs_storage._connection.drop_database(gridfs_storage.database)

        self.store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                               port=settings.MONGODB_CONFIG['port'],
                               database=settings.MONGODB_CONFIG['database'],
                               collection=settings.MONGODB_CONFIG['analysis_collection'])

        self.user = User.objects.all()[0]

        self.search_url = reverse('search')
        try:
            shutil.rmtree(settings.INDEX_PATH)
        except OSError:
            pass

    def tearDown(self):
        gridfs_storage._connection.drop_database(gridfs_storage.database)
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
        _create_corpus_and_documents(owner=self.user)

        management.call_command('update_index')
        # should not index since there is no 'text' for these documents
        for document in Document.objects.all():
            self.assertFalse(document.indexed)

        _update_documents_text_property(store=self.store)
        management.call_command('update_index') # now will index
        for document in Document.objects.all():
            self.assertTrue(document.indexed)

    def test_search_should_work(self):
        corpus, doc_1, doc_2 = _create_corpus_and_documents(owner=self.user)
        _update_documents_text_property(store=self.store)
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
        corpus, doc_1, doc_2 = _create_corpus_and_documents(owner=self.user)
        corpus, doc_3, doc_4 = _create_corpus_and_documents(owner=other_user)
        _update_documents_text_property(store=self.store)
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
