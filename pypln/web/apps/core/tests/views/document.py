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

from django.conf import settings
from django.core.urlresolvers import reverse

from core.models import Document
from core.tests.utils import TestWithMongo, create_document

__all__ = ["DocumentPageViewTest", "DocumentDownloadViewTest"]

class DocumentPageViewTest(TestWithMongo):
    fixtures = ['corpus']
    def prepare_storage(self):
        self.document = create_document("document.txt", "This is our content", self.user)
        self.store['id:{}:text'.format(self.document.id)] = "This is our content"
        self.store['id:{}:tokens'.format(self.document.id)] = ["This", "is", "our",
                                                                "content"]
        self.store['id:{}:pos'.format(self.document.id)] = [["This", "DT", 0 ],
                                                            ["is", "VBZ", 5],
                                                            ["our", "PRP$", 8],
                                                            ["content", "NNP", 12]]
        self.store['id:{}:tagset'.format(self.document.id)] = "en-nltk"
        self.store['id:{}:mimetype'.format(self.document.id)] = "text/plain"
        self.store['id:{}:_properties'.format(self.document.id)] = ['text',
                'tokens', 'pos', 'tagset', 'mimetype']

    def setUp(self):
        # We need the file in gridfs, so we'll just save it instead of using
        # the 'document' fixture.
        super(DocumentPageViewTest, self).setUp()
        self.prepare_storage()

    def test_requires_login(self):
        response = self.client.get(reverse('document_page',
            args=(self.document.id, self.document.slug)))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_corpus(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_page',
            args=(999, 'inexistent_document.txt')))
        self.assertEqual(response.status_code, 404)

    def test_shows_existing_document_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_page',
            args=(self.document.id, self.document.slug)))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/document.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_document_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_page',
            args=(self.document.id, self.document.slug)))

        self.assertIn("document", response.context)
        self.assertEqual(response.context["document"], self.document)

    def test_metadata_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_page',
            args=(self.document.id, self.document.slug)))

        self.assertIn("metadata", response.context)
        metadata = response.context["metadata"]
        self.assertIn("language", metadata)
        self.assertIn("mimetype", metadata)

    def test_view_should_find_document_with_slug_that_is_not_unique(self):
        second_document = create_document("document.txt", "This is our content", self.user)
        second_document.slug = self.document.slug
        second_document.save()
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_page',
            args=(second_document.id, second_document.slug)))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/document.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

        self.assertIn("document", response.context)
        self.assertEqual(response.context["document"], second_document)

class DocumentDownloadViewTest(TestWithMongo):
    fixtures = ['corpus']

    def setUp(self):
        # We need the file in gridfs, so we'll just save it instead of using
        # the 'document' fixture.
        super(DocumentDownloadViewTest, self).setUp()
        self.document = create_document("document.txt", "This is our content", self.user)

    def test_requires_login(self):
        response = self.client.get(reverse('document_download',
            args=(self.document.id, self.document.slug)))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_corpus(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_download',
            args=(999, 'inexistent_document.txt')))
        self.assertEqual(response.status_code, 404)

    def test_shows_existing_document_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_download',
            args=(self.document.id, self.document.slug)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertEqual(response["Content-Disposition"],
                ("attachment; filename={}".format(
                    self.document.blob.name.split('/')[-1])))

    def test_view_should_find_document_with_slug_that_is_not_unique(self):
        second_document = create_document("document.txt", "This is our content", self.user)
        second_document.slug = self.document.slug
        second_document.save()
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_download',
            args=(second_document.id, second_document.slug)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertEqual(response["Content-Disposition"],
                ("attachment; filename={}".format(
                    second_document.blob.name.split('/')[-1])))
