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
from mongodict import MongoDict
from StringIO import StringIO

from django.test import TestCase
from django.conf import settings
from django.core.files import File
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User

from core.models import Corpus, Document
from core.models import gridfs_storage

def create_document(filename, contents, owner):
    fp = StringIO()
    fp.write(contents)
    fp.seek(0)
    fp.name = filename
    fp.size = len(contents.encode('utf-8')) # seriously, Django?

    document = Document(slug=filename, owner=owner,
            date_uploaded=datetime.now(), indexed=False)
    document.blob.save(filename, File(fp))
    document.save()
    return document

def create_corpus_and_documents(owner):
    document_1_text = u'this is the first test.\n'
    document_2_text = u'this is the second test.\n'
    document_1 = create_document(filename='/doc-1.txt', owner=owner,
            contents=document_1_text)
    document_2 = create_document(filename='/doc-2.txt', owner=owner,
            contents=document_2_text)

    now = datetime.now()
    corpus = Corpus(name='Test', slug='test', owner=owner,
            date_created=now, last_modified=now)
    corpus.save()
    corpus.documents.add(document_1)
    corpus.documents.add(document_2)
    corpus.save()

    return corpus, document_1, document_2

def update_documents_text_property(store):
    for document in Document.objects.all():
        text = document.blob.read()
        store['id:{}:text'.format(document.id)] = text
        store['id:{}:_properties'.format(document.id)] = ['text']


class TestWithMongo(TestCase):
    def setUp(self):
        if 'test' not in gridfs_storage.database:
            error_message = ("We expect the mongodb database name to contain the "
                "string 'test' to make sure you don't mess up your production "
                "database. Are you sure you're using settings.test to run these "
                "tests?")
            raise ImproperlyConfigured(error_message)

        gridfs_storage._connection.drop_database(gridfs_storage.database)

        self.store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                               port=settings.MONGODB_CONFIG['port'],
                               database=settings.MONGODB_CONFIG['database'],
                               collection=settings.MONGODB_CONFIG['analysis_collection'])

        self.user = User.objects.all()[0]

    def tearDown(self):
        gridfs_storage._connection.drop_database(gridfs_storage.database)
