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

from datetime import datetime
from io import StringIO

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client


USERNAME = 'testuser'
PASSWORD = 'toostrong'
EMAIL = 'test@user.com'

class TestSearchPage(TestCase):
    def setUp(self):
        self.user = User(username=USERNAME, email=EMAIL, password=PASSWORD)
        self.user.set_password(PASSWORD) #XXX: WTF, Pinax?
        self.user.save()
        self.search_url = reverse('search')

    def test_requires_login(self):
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.has_header('Location'))
        self.assertEqual(response.get('Location', ''),
                         'http://testserver/account/login/?next=/search')

        self.client.login(username=USERNAME, password=PASSWORD)
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
