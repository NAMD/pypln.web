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

__all__ = ["VisualizationRoutingViewTest"]

class VisualizationRoutingViewTest(TestWithMongo):
    fixtures = ['document']

    def prepare_storage(self):
        self.document = Document.objects.all()[0]
        self.store['id:{}:text'.format(self.document.id)] = "This is our content"
        self.store['id:{}:freqdist'.format(self.document.id)] = [["this", 1], ["is", 1],
                                                                 ["content", 1], ["our", 1]]
        self.store['id:{}:language'.format(self.document.id)] = "en"
        self.store['id:{}:_properties'.format(self.document.id)] = ['text', 'freqdist',
                                                                    'language']

    def setUp(self):
        super(VisualizationRoutingViewTest, self).setUp()
        self.prepare_storage()

    def test_raises_404_for_inexistent_visualization(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'document.txt',
                                            'visualization_slug': 'invalid',
                                            'fmt': 'html'}))
        self.assertEqual(response.status_code, 404)

    def test_raises_404_for_existing_visualization_with_invalid_extension(self):
        """This extension exists for other visualizations, but not for this
        one. The request should be answered with 404."""
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_visualization',
                                    kwargs={'document_slug': 'document.txt',
                                            'visualization_slug': 'word-cloud',
                                            'fmt': 'txt'}))
        self.assertEqual(response.status_code, 404)
