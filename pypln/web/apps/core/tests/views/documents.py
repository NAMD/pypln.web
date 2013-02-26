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

import datetime
from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse

from core.models import Corpus, Document
from core.forms import DocumentForm
from core.tests.utils import TestWithMongo, create_document

__all__ = ["DocumentListViewTest"]

class DocumentListViewTest(TestWithMongo):
    fixtures = ['corpus']

    def setUp(self):
        super(DocumentListViewTest, self).setUp()
        self.document = create_document("document.txt", "This is our content", self.user)

    def test_requires_login(self):
        response = self.client.get(reverse('document_list'))
        self.assertEqual(response.status_code, 302)
        login_url = settings.LOGIN_URL
        self.assertTrue(login_url in response['Location'])

    def test_shows_existing_documents_without_error(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/documents.html")
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_documents_are_in_context(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'))

        expected_documents = list(Document.objects.filter(owner=self.user))

        self.assertIn("documents", response.context)
        self.assertEqual(list(response.context["documents"]), expected_documents)
