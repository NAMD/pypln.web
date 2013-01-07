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

from django.core.files.base import ContentFile

from pypln.web.apps.core.models import Document
from pypln.web.apps.core.tests.utils import TestWithMongo

__all__ = ["DocumentModelTest"]

class DocumentModelTest(TestWithMongo):
    fixtures = ['corpus']

    def setUp(self):
        super(DocumentModelTest, self).setUp()
        self.file = ContentFile("Bring us a shrubbery!")
        self.file.name = "42.txt"

    def test_saving_should_generate_a_slug(self):
        doc = Document(owner=self.user, blob=self.file)
        doc.save()
        self.assertEqual(doc.slug, "42.txt")

    def test_saving_another_file_with_the_same_name_should_generate_new_slug(self):
        doc = Document(owner=self.user, blob=self.file)
        doc.save()
        self.assertEqual(doc.slug, "42.txt")

        other_file = ContentFile("Bring us another shrubbery!")
        other_file.name = "42.txt"
        other_doc = Document(owner=self.user, blob=other_file)
        other_doc.save()
        self.assertEqual(other_doc.slug, "42_1.txt")

    def test_editing_a_file_should_not_alter_slug(self):
        doc = Document(owner=self.user, blob=self.file)
        doc.save()
        self.assertEqual(doc.slug, "42.txt")
        doc.date_uploaded = datetime.now()
        doc.save()
        self.assertEqual(doc.slug, "42.txt")

