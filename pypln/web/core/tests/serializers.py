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
import json
from StringIO import StringIO

from django.contrib.auth.models import User
from django.test import TestCase

from pypln.web.core.models import Document
from pypln.web.core.serializers import DocumentSerializer

__all__ = ["DocumentSerializerTest"]

class DocumentSerializerTest(TestCase):
    """
    This is supposed to test the behaviour we added to the serializer. We
    don't really need to test all the serializer behaviour since this is tested
    by the framework itself.
    """
    fixtures = ['users', 'corpora', 'documents']

    def test_corpora_queryset_only_includes_users_corpora(self):
        user = User.objects.get(username="user")
        document = user.document_set.all()[0]
        serializer = DocumentSerializer(document)
        expected_corpora = list(user.corpus_set.all())
        self.assertEqual(list(serializer.fields['corpus'].queryset),
                expected_corpora)

    def test_serializer_needs_either_a_document_or_a_context(self):
        """
        This may change in the future, but for now `DocumentSerializer` needs
        to know the owner of the document, and that means either receiving an
        already existing `Document` instance or being instantiated with a
        resquest in the context (and a `User` in this request). This works for us
        right now because every request has to be authenticated. It would not
        work if we had to parse data from an unauthenticated user.
        """
        with self.assertRaises(ValueError):
            DocumentSerializer()
