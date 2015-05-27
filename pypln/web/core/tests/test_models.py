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
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.db import IntegrityError
from django.test import TestCase

from mongodict import MongoDict

from pypln.web.core.models import Corpus, Document
from pypln.web.core.tests.utils import TestWithMongo

__all__ = ["CorpusModelTest", "DocumentModelTest"]

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


class DocumentModelTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents']

    def test_get_properties_from_store(self):
        expected_data = ["average_sentence_length", "average_sentence_repertoire",
            "contents", "file_id", "file_metadata", "filename", "forced_decoding",
            "freqdist", "language", "length", "md5", "mimetype", "momentum_1",
            "momentum_2", "momentum_3", "momentum_4", "palavras_raw_ran", "pos",
            "repertoire", "sentences", "tagset", "text", "tokens", "upload_date"]
        document = Document.objects.all()[0]
        self.assertEqual(document.properties.keys(), expected_data)

    def test_get_text_from_store(self):
        expected_data = u'This is a test file.'
        document = Document.objects.all()[0]
        self.assertEqual(document.properties['text'], expected_data)
