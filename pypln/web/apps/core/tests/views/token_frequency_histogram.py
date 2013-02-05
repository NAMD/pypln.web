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
from core.tests.utils import TestWithMongo

__all__ = ["TokenFrequencyHistogramViewTest"]

class TokenFrequencyHistogramViewTest(TestWithMongo):
    fixtures = ['document']

    def prepare_storage(self):
        self.document = Document.objects.all()[0]
        self.store['id:{}:freqdist'.format(self.document.id)] = [["this", 1], ["is", 1],
                                                                 ["content", 1], ["our", 1]]
        self.store['id:{}:momentum_1'.format(self.document.id)] = 1
        self.store['id:{}:momentum_2'.format(self.document.id)] = 1
        self.store['id:{}:momentum_3'.format(self.document.id)] = 1
        self.store['id:{}:momentum_4'.format(self.document.id)] = 1
        self.store['id:{}:_properties'.format(self.document.id)] = ['freqdist', 'momentum_1',
                                                                    'momentum_2', 'momentum_3',
                                                                    'momentum_4']
    def setUp(self):
        super(TokenFrequencyHistogramViewTest, self).setUp()
        self.prepare_storage()

    def test_requires_login(self):
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'document.txt',
            'visualization_slug': 'token-frequency-histogram', 'fmt': 'html'}))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_raises_404_for_inexistent_document(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'inexistent-document.txt',
            'visualization_slug': 'token-frequency-histogram', 'fmt': 'html'}))
        self.assertEqual(response.status_code, 404)

    def test_shows_text_for_existing_document_in_html_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'document.txt',
            'visualization_slug': 'token-frequency-histogram', 'fmt': 'html'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/visualizations/token-frequency-histogram.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_shows_text_for_existing_document_in_txt_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'document.txt',
            'visualization_slug': 'token-frequency-histogram', 'fmt': 'csv'}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/visualizations/token-frequency-histogram.csv")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertEqual(response['Content-Disposition'], ('attachment; '
                    'filename="document.txt-token-frequency-histogram.csv"'))

    def test_expected_data_is_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'document.txt',
            'visualization_slug': 'token-frequency-histogram', 'fmt': 'html'}))

        self.assertIn("document", response.context)
        document = Document.objects.all()[0]
        self.assertEqual(response.context["document"], document)
        self.assertIn("values", response.context)
        self.assertIn("momentum_1", response.context)
        self.assertIn("momentum_2", response.context)
        self.assertIn("momentum_3", response.context)
        self.assertIn("momentum_4", response.context)
