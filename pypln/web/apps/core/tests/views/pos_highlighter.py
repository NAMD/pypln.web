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
from core.tests.utils import TestWithMongo

__all__ = ["PosHighlighterViewTest"]

class PosHighlighterViewTest(TestWithMongo):
    fixtures = ['document']

    def prepare_storage(self):
        document = Document.objects.all()[0]
        self.store['id:{}:text'.format(document.id)] = "This is our content"
        self.store['id:{}:tokens'.format(document.id)] = ["This", "is", "our",
                                                            "content"]
        self.store['id:{}:pos'.format(document.id)] = [["This", "DT", 0 ],
                                                       ["is", "VBZ", 5],
                                                       [ "our", "PRP$", 8],
                                                       ["content", "NNP", 12]]
        self.store['id:{}:_properties'.format(document.id)] = ['text', 'tokens', 'pos']

    def setUp(self):
        super(PosHighlighterViewTest, self).setUp()
        self.prepare_storage()

    def test_requires_login(self):
        response = self.client.get(reverse('pos_highlighter_visualization',
            kwargs={'document_slug': 'document.txt', 'fmt': 'html'}))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_document(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('pos_highlighter_visualization',
            kwargs={'document_slug': 'inexistent-document.txt', 'fmt': 'html'}))
        self.assertEqual(response.status_code, 404)

    def test_shows_highlight_for_existing_document_in_html_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('pos_highlighter_visualization',
            kwargs={'document_slug': 'document.txt', 'fmt': 'html'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/visualizations/pos-highlighter.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_shows_highlight_for_existing_document_in_csv_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('pos_highlighter_visualization',
            kwargs={'document_slug': 'document.txt', 'fmt': 'csv'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/visualizations/pos-highlighter.csv")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertEqual(response['Content-Disposition'], ('attachment; '
                    'filename="document.txt-part-of-speech.csv"'))

    def test_expected_data_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('pos_highlighter_visualization',
            kwargs={'document_slug': 'document.txt', 'fmt': 'html'}))

        self.assertIn("document", response.context)
        document = Document.objects.all()[0]
        self.assertEqual(response.context["document"], document)

        self.assertIn("pos", response.context)
        self.assertIn("tagset", response.context)
        self.assertIn("most_common", response.context)
        self.assertIn("token_list", response.context)
