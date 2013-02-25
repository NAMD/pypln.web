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
import datetime
from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from core.models import Corpus, Document
from core.forms import DocumentForm
from core.tests.utils import create_document

__all__ = ["CorpusViewTest", "UploadDocumentTest", "CorpusViewPaginationTest"]

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
        start_time = datetime.datetime.now()
        corpus = Corpus.objects.get(slug="test-corpus")
        self.assertLess(corpus.last_modified, start_time)
        response = self.client.post(self.url, {'blob': [self.fp]}, follow=True)
        corpus = Corpus.objects.get(slug="test-corpus")
        self.assertGreater(corpus.last_modified, start_time)

    @patch('core.views.create_pipelines')
    def test_pipeline_is_created(self, create_pipelines_mock):
        self.client.login(username="admin", password="admin")
        response = self.client.post(self.url, {'blob': [self.fp]}, follow=True)
        document = Document.objects.all()[0]
        expected_data = [{'_id': str(document.blob.file._id), 'id': document.id}]

        self.assertTrue(create_pipelines_mock.called)
        self.assertIn(expected_data, create_pipelines_mock.call_args[0])


class CorpusViewPaginationTest(TestCase):
    fixtures = ['corpus']

    def _create_documents(self, n):
        for i in range(n):
            doc = create_document("document_{}".format(i),
                    "content", self.user)
            self.corpus.documents.add(doc)

    def setUp(self):
        self.user = User.objects.all()[0]
        self.corpus = Corpus.objects.filter(owner=self.user)[0]


    def test_list_should_use_default_number_of_documents_per_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}))

        expected_document_list = list(self.corpus.documents.all()[:10])

        self.assertIn("documents", response.context)

        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_list_should_show_second_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'page': 2})

        expected_document_list = list(self.corpus.documents.all()[10:])

        self.assertIn("documents", response.context)

        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_ignores_page_parameter_if_not_an_integer(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'page': 'invalid'})

        expected_document_list = list(self.corpus.documents.all()[:10])

        self.assertIn("documents", response.context)

        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_show_last_page_if_request_is_out_of_range(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'page': 9999})

        expected_document_list = list(self.corpus.documents.all()[10:])

        self.assertIn("documents", response.context)

        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_user_can_define_number_of_objects_per_page(self):
        self._create_documents(5)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'per_page': 2})

        self.assertIn("documents", response.context)

        paginator = response.context["documents"].paginator
        self.assertEqual(paginator.num_pages, 3)

    def test_ignores_invalid_number_of_objects_per_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'per_page': 'invalid'})

        self.assertIn("documents", response.context)

        paginator = response.context["documents"].paginator
        self.assertEqual(paginator.num_pages, 2)

    def test_ignores_number_of_objects_per_page_if_it_is_zero(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'per_page': 0})

        self.assertIn("documents", response.context)

        paginator = response.context["documents"].paginator
        self.assertEqual(paginator.num_pages, 2)

    def test_ignore_invalid_sort_key_and_sort_by_blob_name(self):
        self.corpus.documents.add(create_document("z", "content", self.user))
        self._create_documents(2)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'sort_by': 'invalid'})
        expected_document_list = list(self.corpus.documents.order_by('blob'))
        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)

    def test_sort_by_blob_name_by_default(self):
        # create a document that should appear last, but without explicitly
        # sorting by filename it will appear first
        self.corpus.documents.add(create_document("z", "content", self.user))
        self._create_documents(2)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}))
        expected_document_list = list(self.corpus.documents.order_by('blob'))
        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)

    def test_sort_by_blob_name(self):
        self.corpus.documents.add(create_document("z", "content", self.user))
        self._create_documents(2)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'sort_by': 'filename'})
        expected_document_list = list(self.corpus.documents.order_by('blob'))
        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)

    def test_reverse_sort_by_blob_name(self):
        self.corpus.documents.add(create_document("z", "content", self.user))
        self._create_documents(2)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'sort_by': 'filename_desc'})
        expected_document_list = list(self.corpus.documents.order_by('-blob'))
        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)

    def test_sort_by_date_uploaded(self):
        doc_1 = create_document("z", "1", self.user)
        doc_1.date_uploaded = datetime.date(2013, 1, 1)
        doc_1.save()
        self.corpus.documents.add(doc_1)
        doc_2 = create_document("a", "1", self.user)
        doc_2.date_uploaded = datetime.date(2013, 1, 10)
        doc_2.save()
        self.corpus.documents.add(doc_2)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'sort_by': 'date'})
        expected_document_list = list(self.corpus.documents.order_by('date_uploaded'))
        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)

    def test_reverse_sort_by_date_uploaded(self):
        doc_1 = create_document("z", "1", self.user)
        doc_1.date_uploaded = datetime.date(2013, 1, 10)
        doc_1.save()
        self.corpus.documents.add(doc_1)
        doc_2 = create_document("a", "1", self.user)
        doc_2.date_uploaded = datetime.date(2013, 1, 1)
        doc_2.save()
        self.corpus.documents.add(doc_2)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'}), {'sort_by': 'date_desc'})
        expected_document_list = list(self.corpus.documents.order_by('-date_uploaded'))
        self.assertEqual(list(response.context["documents"].object_list),
                expected_document_list)
