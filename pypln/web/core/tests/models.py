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

from pypln.web.core.models import Corpus, Document, StoreProxy
from pypln.web.core.tests.utils import TestWithMongo

__all__ = ["CorpusModelTest", "DocumentModelTest", "StoreProxyTest"]

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

    def test_document_should_instantiate_a_store_when_needed(self):
        document = Document.objects.all()[0]
        self.assertIsNone(document._store)
        document.properties.keys()
        self.assertEqual(document._store, self.store)

    def test_get_properties_from_store(self):
        expected_data = ["mimetype", "freqdist", "average_sentence_repertoire",
            "language", "average_sentence_length", "sentences", "momentum_1",
            "pos", "momentum_3", "file_metadata", "tokens", "repertoire",
            "text", "tagset", "momentum_4", "momentum_2"]
        document = Document.objects.all()[0]
        self.assertEqual(document.properties.keys(), expected_data)

    def test_get_text_from_store(self):
        expected_data = u'This is a test file with some test text.'
        document = Document.objects.all()[0]
        self.assertEqual(document.properties['text'], expected_data)

    def test_access_store_for_a_document_that_has_no_id_yet(self):
        corpus = Corpus.objects.all()[0]
        document = Document(blob=File(StringIO(), "filename"), owner=corpus.owner,
                corpus=corpus)

        with self.assertRaises(ValueError):
            document.properties.keys()

    def test_access_store_for_a_document_that_does_not_have_entries_in_mongo(self):
        corpus = Corpus.objects.all()[0]
        document = Document.objects.create(blob=File(StringIO(), "filename"),
                owner=corpus.owner, corpus=corpus)

        with self.assertRaises(KeyError):
            document.properties.keys()


class StoreProxyTest(TestWithMongo):
    fixtures = ['users', 'corpora', 'documents']

    def setUp(self):
        self.document = Document.objects.all()[0]
        self.base_store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                   port=settings.MONGODB_CONFIG['port'],
                   database=settings.MONGODB_CONFIG['database'],
                   collection=settings.MONGODB_CONFIG['analysis_collection'])
        self.proxy = StoreProxy(self.document.id, self.base_store)

    def test_access_store_data_without_formating_the_key_with_document_id(self):
        self.assertEqual(self.proxy['text'],
                self.base_store['id:{}:text'.format(self.document.id)])

    def test_list_keys_based_on_the_available_properties(self):
        self.assertEqual(self.proxy.keys(),
                self.base_store['id:{}:_properties'.format(self.document.id)])

    def test_only_lists_items_in_store_that_are_related_from_this_document(self):
        """
        Since we're using UserDict.DictMixin as a parent class of
        StoreProxy, this behaviour comes from implementing the `keys` method.
        """
        expected_items = [(k.split(':')[-1], v) for k, v in self.base_store.items() if
                int(k.split(':')[1]) == self.document.id and k.split(':')[-1]
                != u'_properties']

        self.assertItemsEqual(self.proxy.items(), expected_items)

    def test_proxy_is_read_only(self):
        with self.assertRaises(AttributeError):
            self.proxy["new key"] = "new value"

    def test_access_store_keys_for_a_document_that_does_not_have_entries_in_mongo(self):
        corpus = Corpus.objects.all()[0]
        document = Document.objects.create(blob=File(StringIO(), "filename"),
                owner=corpus.owner, corpus=corpus)

        with self.assertRaisesRegexp(KeyError, "Can't find information for "
                "document with id"):
            document.properties.keys()

    def test_access_inexistent_key_for_a_document_that_has_entries_in_mongo(self):
        document = Document.objects.all()[0]

        with self.assertRaisesRegexp(KeyError, "Can't find key .* for "
                "document with id .*$"):
            document.properties['invalid_key']
