"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from core.models import Corpus, DocumentForm


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
