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
from django.core import mail
from django.core.urlresolvers import reverse

from core.models import Document
from core.tests.utils import TestWithMongo, create_document

__all__ = ["TextVisualizationViewTest"]

class TextVisualizationViewTest(TestWithMongo):
    fixtures = ['document']

    def _update_document_data(self, document):
        self.store['id:{}:text'.format(document.id)] = "This is our content"
        self.store['id:{}:_properties'.format(document.id)] = ['text',
                                                               'tokens',
                                                               'pos']

    def prepare_storage(self):
        self.document = Document.objects.all()[0]
        self._update_document_data(self.document)

    def setUp(self):
        super(TextVisualizationViewTest, self).setUp()
        self.prepare_storage()

    def test_requires_login(self):
        response = self.client.get(reverse('document_visualization',
            kwargs={'document_id': self.document.id, 'document_slug': 'document.txt',
                'visualization_slug': 'text', 'fmt': 'html'}))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_document(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
            kwargs={'document_id': 999, 'document_slug': 'inexistent-document.txt',
                'visualization_slug': 'text', 'fmt': 'html'}))
        self.assertEqual(response.status_code, 404)

    def test_shows_text_for_existing_document_in_html_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
            kwargs={'document_id': self.document.id, 'document_slug': 'document.txt',
                'visualization_slug': 'text', 'fmt': 'html'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/visualizations/text.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_shows_text_for_existing_document_in_txt_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
            kwargs={'document_id': self.document.id, 'document_slug': 'document.txt',
                'visualization_slug': 'text', 'fmt': 'txt'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/visualizations/text.txt")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEqual(response['Content-Disposition'], ('attachment; '
                    'filename="document.txt-text.txt"'))

    def test_expected_data_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
            kwargs={'document_id': self.document.id, 'document_slug': 'document.txt',
                'visualization_slug': 'text', 'fmt': 'html'}))

        self.assertIn("document", response.context)
        document = Document.objects.all()[0]
        self.assertEqual(response.context["document"], document)
        self.assertIn("text", response.context)

    def test_visualization_should_work_for_different_documents_with_the_same_slug(self):
        # We need to simulate the same document being uploaded again
        document = create_document("document.txt", "This is our content", self.user)
        self._update_document_data(document)

        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
            kwargs={'document_id': document.id, 'document_slug': 'document.txt',
                'visualization_slug': 'text', 'fmt': 'html'}))

        self.assertIn("document", response.context)
        self.assertEqual(response.context["document"], document)

        self.assertIn("text", response.context)
