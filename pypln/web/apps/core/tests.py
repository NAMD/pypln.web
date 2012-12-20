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

from django.test import TestCase
from django.test.client import RequestFactory
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings

from django.contrib.auth.models import User

from core.models import Corpus, Document
from core.forms import DocumentForm


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

        self.assertEqual(len(Document.objects.all()), 1)

        response = self.client.post(self.url, {'blob': self.fp}, follow=True)

        message = list(response.context["messages"])[0].message
        self.assertEqual("1 document uploaded successfully!", message)
        self.assertEqual(len(Document.objects.all()), 2)

    def test_uploads_multiple_files(self):
        self.client.login(username="admin", password="admin")

        self.assertEqual(len(Document.objects.all()), 1)

        response = self.client.post(self.url, {'blob': [self.fp, self.fp2]}, follow=True)

        message = list(response.context["messages"])[0].message
        self.assertEqual("2 documents uploaded successfully!", message)
        self.assertEqual(len(Document.objects.all()), 3)

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
        self.assertEqual(len(Document.objects.all()), 1)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save()
        self.assertEqual(docs[0].owner, self.user)
        self.assertEqual(len(Document.objects.all()), 2)

    def test_save_raises_ValueError_if_data_isnt_valid(self):
        self.assertEqual(len(Document.objects.all()), 1)
        request = self.request_factory.post(self.url, {"blob": []})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertRaises(ValueError, form.save)

    def test_form_only_returns_document_if_commit_is_false(self):
        self.assertEqual(len(Document.objects.all()), 1)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save(commit=False)
        self.assertEqual(docs[0].owner, self.user)
        self.assertEqual(len(Document.objects.all()), 1)

    def test_blob_widget_has_multiple_attr(self):
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertEqual(form.fields['blob'].widget.attrs['multiple'],
                         'multiple')

    def test_form_saves_more_than_one_document(self):
        self.assertEqual(len(Document.objects.all()), 1)
        request = self.request_factory.post(self.url, {"blob": [self.fp, self.fp2]})
        form = DocumentForm(self.user, request.POST, request.FILES)
        form.is_valid()
        form.save()
        self.assertEqual(len(Document.objects.all()), 3)
