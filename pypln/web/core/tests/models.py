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
from django.db import IntegrityError
from django.test import TestCase

from pypln.web.core.models import Corpus

__all__ = ["CorpusModelTest"]

class CorpusModelTest(TestCase):
    fixtures = ['users']

    def test_cant_create_two_corpora_with_the_same_name_for_the_same_user(self):
        user = User.objects.get(username="user")
        corpus_1 = Corpus.objects.create(owner=user, name="Corpus")
        with self.assertRaises(IntegrityError):
            Corpus.objects.create(owner=user, name="Corpus")

    def test_different_users_can_have_corpora_with_the_same_name(self):
        user = User.objects.get(username="user")
        admin = User.objects.get(username="admin")
        corpus_1 = Corpus.objects.create(owner=user, name="Corpus")
        corpus_2 = Corpus.objects.create(owner=admin, name="Corpus")
        self.assertEqual(corpus_1.name, corpus_2.name)
