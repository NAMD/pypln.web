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

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response

from pypln.web.core.models import Corpus, Document
from pypln.web.core.serializers import CorpusSerializer, DocumentSerializer

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'corpora': reverse('corpus-list', request=request),
        'documents': reverse('document-list', request=request),
    })

class CorpusList(generics.ListCreateAPIView):
    model = Corpus
    serializer_class = CorpusSerializer

    def pre_save(self, obj):
        obj.owner = self.request.user

class CorpusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Corpus
    serializer_class = CorpusSerializer

    def pre_save(self, obj):
        obj.owner = self.request.user

class DocumentList(generics.ListCreateAPIView):
    model = Document
    serializer_class = DocumentSerializer

    def pre_save(self, obj):
        obj.owner = self.request.user

class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Document
    serializer_class = DocumentSerializer

    def pre_save(self, obj):
        obj.owner = self.request.user
