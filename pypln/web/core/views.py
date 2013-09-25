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

from django.http import Http404

from rest_framework import generics
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework import serializers

from pypln.web.backend_adapter.pipelines import create_pipeline
from pypln.web.core.models import Corpus, Document
from pypln.web.core.serializers import CorpusSerializer, DocumentSerializer
from pypln.web.core.serializers import PropertyListSerializer

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'corpora': reverse('corpus-list', request=request),
        'documents': reverse('document-list', request=request),
    })

class CorpusList(generics.ListCreateAPIView):
    """
    Lists all corpora available to the current user and creates new corpora.

    `GET` requests will simply list all available corpora.

    `POST` requests will create a new corpus and require:

    - `name`: A string that will be used as the corpus' name (at most 60 chars).
    - `description`: A short (at most 255 chars) description of the new corpus.

    The list will only include corpora owned by the requesting user, and a
    newly created corpus will always have the user that sent the `POST` request
    as it's owner.
    """
    model = Corpus
    serializer_class = CorpusSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Corpus.objects.filter(owner=self.request.user)

    def pre_save(self, obj):
        if Corpus.objects.filter(name=obj.name,
                owner=self.request.user).exists():
            raise ParseError(detail="Corpora names must be unique for each user.")
        else:
            obj.owner = self.request.user

class CorpusDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Corpus
    serializer_class = CorpusSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Corpus.objects.filter(owner=self.request.user)

    def pre_save(self, obj):
        if Corpus.objects.filter(name=obj.name,
                owner=self.request.user).exists():
            raise ParseError(detail="Corpora names must be unique for each user.")
        else:
            obj.owner = self.request.user

class DocumentList(generics.ListCreateAPIView):
    model = Document
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user

    def post_save(self, obj, created):
        data = {"_id": str(obj.blob.file._id), "id": obj.id}
        create_pipeline(data)

class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Document
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user

class PropertyList(generics.RetrieveAPIView):
    serializer_class = PropertyListSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

class PropertyDetail(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self, *args, **kwargs):
        doc = super(PropertyDetail, self).get_object(*args, **kwargs)
        prop = self.kwargs['property']
        if prop in doc.properties:
            return doc
        else:
            raise Http404("Property '{}' does not exist for document "
                    "{}.".format(prop, doc))

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def get_serializer_class(self, *args, **kwargs):
        class PropertySerializer(serializers.Serializer):
            value = serializers.Field(source="properties.{}".format(
                self.kwargs['property']))
        return PropertySerializer
