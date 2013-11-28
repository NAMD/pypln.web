# -*- coding:utf-8 -*-
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
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework.authtoken.models import Token

__all__ = ["AuthTokenViewTest"]


class AuthTokenViewTest(TestCase):
    fixtures = ['users']

    def test_requires_login(self):
        response = self.client.get(reverse('auth_token'))
        self.assertEqual(response.status_code, 403)

    def test_lists_the_authenticated_users_token(self):
        self.client.login(username="user", password="user")
        response = self.client.get(reverse('auth_token'))
        self.assertEqual(response.status_code, 200)

        expected_data = Token.objects.get(
                user=User.objects.get(username="user")).key
        self.assertEqual(response.data['token'], expected_data)
