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

from core.models import gridfs_storage, Corpus, Document
from core.forms import DocumentForm
from core import views

class CorpusViewTest(TestCase):
    fixtures = ['corpus']
    def test_requires_login(self):
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_corpus(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'corpus-that-isnt-there'}))
        self.assertEqual(response.status_code, 404)

    def test_shows_existing_corpus_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/corpus.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_corpus_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}))

        corpus = Corpus.objects.get(slug="test-corpus")

        self.assertIn("corpus", response.context)
        self.assertEqual(response.context["corpus"], corpus)

    def test_document_upload_form_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}))

        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], DocumentForm)

class UploadDocumentTest(TestCase):
    fixtures = ['corpus']

    def setUp(self):
        self.url = reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'})
        self.user = User.objects.all()[0]

        self.fp = StringIO("Bring us a shrubbery!!")
        self.fp.name = "42.txt"

        self.fp2 = StringIO("Bring us another shrubbery!!")
        self.fp2.name = "43.txt"

        self.request_factory = RequestFactory()

    def tearDown(self):
        self.fp.close()
        self.fp2.close()

    def test_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_corpus(self):
        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse('corpus_page',
            kwargs={'corpus_slug': 'corpus-that-isnt-there'}))
        self.assertEqual(response.status_code, 404)

    def test_error_uploading_no_files(self):
        self.client.login(username="admin", password="admin")

        response = self.client.post(self.url, {'blob': []}, follow=True)
        self.assertFormError(response, "form", "blob", ["This field is required."])

    def test_uploads_a_single_file(self):
        self.client.login(username="admin", password="admin")

        self.assertEqual(len(Document.objects.all()), 0)

        response = self.client.post(self.url, {'blob': self.fp}, follow=True)

        message = list(response.context["messages"])[0].message
        self.assertEqual("1 document uploaded successfully!", message)
        self.assertEqual(len(Document.objects.all()), 1)

    def test_uploads_multiple_files(self):
        self.client.login(username="admin", password="admin")

        self.assertEqual(len(Document.objects.all()), 0)

        response = self.client.post(self.url, {'blob': [self.fp, self.fp2]}, follow=True)

        message = list(response.context["messages"])[0].message
        self.assertEqual("2 documents uploaded successfully!", message)
        self.assertEqual(len(Document.objects.all()), 2)

    def test_corpus_is_associated_to_document_after_upload(self):
        self.client.login(username="admin", password="admin")

        response = self.client.post(self.url, {'blob': [self.fp]}, follow=True)
        corpus = Corpus.objects.get(slug="test-corpus")
        document = Document.objects.all()[0]
        self.assertIn(corpus, document.corpus_set.all())

    def test_corpus_last_modified_date_is_updated(self):
        self.client.login(username="admin", password="admin")
        start_time = datetime.now()
        corpus = Corpus.objects.get(slug="test-corpus")
        self.assertLess(corpus.last_modified, start_time)
        response = self.client.post(self.url, {'blob': [self.fp]}, follow=True)
        corpus = Corpus.objects.get(slug="test-corpus")
        self.assertGreater(corpus.last_modified, start_time)

    @patch('core.views.create_pipeline')
    def test_pipeline_is_created(self, create_pipeline_mock):
        self.client.login(username="admin", password="admin")
        response = self.client.post(self.url, {'blob': [self.fp]}, follow=True)
        document = Document.objects.all()[0]
        expected_data = {'_id': str(document.blob.file._id), 'id': document.id}

        self.assertTrue(create_pipeline_mock.called)
        self.assertIn(expected_data, create_pipeline_mock.call_args[0])

class DocumentFormTest(TestCase):
    fixtures = ['corpus']

    def setUp(self):
        self.url = reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'})
        self.user = User.objects.all()[0]

        self.fp = StringIO("Bring us a shrubbery!!")
        self.fp.name = "42.txt"

        self.fp2 = StringIO("Bring us another shrubbery!!")
        self.fp2.name = "43.txt"

        self.request_factory = RequestFactory()

    def tearDown(self):
        self.fp.close()
        self.fp2.close()

    def test_form_is_valid_with_one_file(self):
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertTrue(form.is_valid())

    def test_at_least_one_file_is_required(self):
        request = self.request_factory.post(self.url, {"blob": []})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertFalse(form.is_valid())

    def test_form_is_valid_with_multiple_files(self):
        request = self.request_factory.post(self.url,
                                            {"blob": [self.fp, self.fp2]})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertTrue(form.is_valid())

    def test_form_saves_document_with_correct_user(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save()
        self.assertEqual(docs[0].owner, self.user)
        self.assertEqual(len(Document.objects.all()), 1)

    def test_form_saves_document_with_correct_content(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save()
        self.assertEqual(len(Document.objects.all()), 1)
        doc = Document.objects.all()[0]
        self.assertEqual(doc.blob.read(), "Bring us a shrubbery!!")

    def test_save_raises_ValueError_if_data_isnt_valid(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": []})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertRaises(ValueError, form.save)

    def test_form_only_returns_document_if_commit_is_false(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save(commit=False)
        self.assertEqual(docs[0].owner, self.user)
        self.assertEqual(len(Document.objects.all()), 0)

    def test_blob_widget_has_multiple_attr(self):
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertEqual(form.fields['blob'].widget.attrs['multiple'],
                         'multiple')

    def test_form_saves_more_than_one_document(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": [self.fp, self.fp2]})
        form = DocumentForm(self.user, request.POST, request.FILES)
        form.is_valid()
        form.save()
        self.assertEqual(len(Document.objects.all()), 2)
        doc1, doc2 = Document.objects.all()
        self.assertEqual(doc1.blob.read(), "Bring us a shrubbery!!")
        self.assertEqual(doc2.blob.read(), "Bring us another shrubbery!!")

class DocumentModelTest(TestCase):
    fixtures = ['corpus']

    def setUp(self):
        if 'test' not in gridfs_storage.database:
            error_message = ("We expect the mongodb database name to contain the "
                "string 'test' to make sure you don't mess up your production "
                "database. Are you sure you're using settings.test to run these "
                "tests?")
            raise ImproperlyConfigured(error_message)

        gridfs_storage._connection.drop_database(gridfs_storage.database)

        self.user = User.objects.all()[0]
        self.file = ContentFile("Bring us a shrubbery!")
        self.file.name = "42.txt"

    def tearDown(self):
        gridfs_storage._connection.drop_database(gridfs_storage.database)

    def test_saving_should_generate_a_slug(self):
        doc = Document(owner=self.user, blob=self.file)
        doc.save()
        self.assertEqual(doc.slug, "42.txt")

    def test_saving_another_file_with_the_same_name_should_generate_new_slug(self):
        doc = Document(owner=self.user, blob=self.file)
        doc.save()
        self.assertEqual(doc.slug, "42.txt")

        other_file = ContentFile("Bring us another shrubbery!")
        other_file.name = "42.txt"
        other_doc = Document(owner=self.user, blob=other_file)
        other_doc.save()
        self.assertEqual(other_doc.slug, "42_1.txt")

    def test_editing_a_file_should_not_alter_slug(self):
        doc = Document(owner=self.user, blob=self.file)
        doc.save()
        self.assertEqual(doc.slug, "42.txt")
        doc.date_uploaded = datetime.now()
        doc.save()
        self.assertEqual(doc.slug, "42.txt")

from django.test.client import Client
from mongodict import MongoDict

from pypln.web.apps.core.models import Corpus, Document, index_schema


USERNAME = 'testuser'
PASSWORD = 'toostrong'
EMAIL = 'test@user.com'

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

    @classmethod
    def setUpClass(cls):
        settings.MONGODB_CONFIG = {'host': 'localhost',
                                   'port': 27017,
                                   'database': 'pypln_test',
                                   'gridfs_collection': 'files',
                                   'analysis_collection': 'analysis',
                                   'monitoring_collection': 'monitoring',
        }
        settings.INDEX_PATH += '_test'
        cls.connection = pymongo.Connection(host=settings.MONGODB_CONFIG['host'],
                port=settings.MONGODB_CONFIG['port'])
        cls.store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                              port=settings.MONGODB_CONFIG['port'],
                              database=settings.MONGODB_CONFIG['database'],
                              collection=settings.MONGODB_CONFIG['analysis_collection'])

    def setUp(self):
        self.connection.drop_database(settings.MONGODB_CONFIG['database'])
        self.user = User(username=USERNAME, email=EMAIL, password=PASSWORD)
        self.user.set_password(PASSWORD) #XXX: WTF, Pinax?
        self.user.save()
        self.search_url = reverse('search')
        try:
            shutil.rmtree(settings.INDEX_PATH)
        except OSError:
            pass

    def tearDown(self):
        self.connection.drop_database(settings.MONGODB_CONFIG['database'])
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

        self.client.login(username=USERNAME, password=PASSWORD)
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

        self.client.login(username=USERNAME, password=PASSWORD)
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
        other_user = User(username=USERNAME + '2', email='some@email.com',
                          password=PASSWORD + '2')
        other_user.set_password(PASSWORD + '2') #XXX: WTF, Pinax?
        other_user.save()
        corpus, doc_1, doc_2 = _create_corpus_and_documents(owner=self.user)
        corpus, doc_3, doc_4 = _create_corpus_and_documents(owner=other_user)
        _update_documents_text_property(store=self.store)
        management.call_command('update_index')

        self.client.login(username=USERNAME, password=PASSWORD)
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

        self.client.login(username=USERNAME + '2', password=PASSWORD + '2')
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
