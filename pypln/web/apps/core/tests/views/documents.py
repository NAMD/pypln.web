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
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from core.models import Corpus, Document
from core.forms import DocumentForm
from core.tests.utils import TestWithMongo, create_document

__all__ = ["DocumentListViewTest", "DocumentListViewPaginationTest"]

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


class DocumentListViewPaginationTest(TestCase):
    fixtures = ['corpus']

    def _create_documents(self, n):
        for i in range(n):
            doc = create_document("document_{}".format(i),
                    "content", self.user)

    def setUp(self):
        self.user = User.objects.all()[0]

    def test_list_should_use_default_number_of_documents_per_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'))

        expected_document_list = list(Document.objects.all()[:10])

        self.assertIn("documents", response.context)
        self.assertEqual(list(response.context["documents"]), expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_list_should_show_second_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'page': 2})

        expected_document_list = list(Document.objects.all()[10:])

        self.assertIn("documents", response.context)
        self.assertEqual(list(response.context["documents"]), expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_returns_404_if_page_parameter_is_not_an_integer(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'page': 'invalid'})

        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_requested_page_is_out_of_range(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'page': 9999})

        self.assertEqual(response.status_code, 404)

    def test_returns_last_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'page': 'last'})

        expected_document_list = list(Document.objects.all()[10:])

        self.assertIn("documents", response.context)
        self.assertEqual(list(response.context["documents"]), expected_document_list)
        self.assertNotIn(settings.TEMPLATE_STRING_IF_INVALID, response.content)

    def test_user_can_define_number_of_objects_per_page(self):
        self._create_documents(5)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'per_page': 2})

        self.assertIn("paginator", response.context)
        paginator = response.context["paginator"]
        self.assertEqual(paginator.num_pages, 3)

    def test_ignores_invalid_number_of_objects_per_page(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'per_page': 'invalid'})

        self.assertIn("paginator", response.context)
        paginator = response.context["paginator"]
        self.assertEqual(paginator.num_pages, 2)

    def test_ignores_number_of_objects_per_page_if_it_is_zero(self):
        self._create_documents(11)
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('document_list'), {'per_page': 0})

        self.assertIn("paginator", response.context)
        paginator = response.context["paginator"]
        self.assertEqual(paginator.num_pages, 2)
