"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from StringIO import StringIO

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings

from core.models import Corpus, Document, DocumentForm


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

        fp = StringIO("Bring us a shrubbery!!")
        fp.name = "42.txt"
        response = self.client.post(self.url, {'blob': fp}, follow=True)
        fp.close()

        message = list(response.context["messages"])[0].message
        self.assertEqual("1 document uploaded successfully!", message)
        self.assertEqual(len(Document.objects.all()), 2)

    def test_uploads_multiple_files(self):
        self.client.login(username="admin", password="admin")

        self.assertEqual(len(Document.objects.all()), 1)

        fp = StringIO("Bring us a shrubbery!!")
        fp.name = "42.txt"
        fp2 = StringIO("Bring us another shrubbery!!")
        fp2.name = "43.txt"
        response = self.client.post(self.url, {'blob': [fp, fp2]}, follow=True)
        fp.close()
        fp2.close()

        message = list(response.context["messages"])[0].message
        self.assertEqual("2 documents uploaded successfully!", message)
        self.assertEqual(len(Document.objects.all()), 3)
