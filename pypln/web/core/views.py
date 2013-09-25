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
    """
    Show details of a specific corpus and allows the corpus to be edited.

    `GET` requests will show all the corpus details:

    - `owner`: the user that owns the corpus.
    - `documents`: a list of all documents in this corpus.
    - `url`: the fully qualified url for this corpus (which should be used as
      an argument when creating new documents).
    - `name`: the corpus name.
    - `description`: the corpus description.
    - `created_at`: the creation date of the corpus.


    `PUT` requests will edit a corpus and require:

    - `name`: A string that will be set as the corpus' name (at most 60 chars).
    - `description`: A short (at most 255 chars) description of the corpus.

    The owner is set automatically to the requesting user, so it is not
    possible to change the owner using this resource.
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

class DocumentList(generics.ListCreateAPIView):
    """
    Lists all documents available to the current user and creates new documents.

    `GET` requests will simply list all available documents.

    `POST` requests will create a new document and require:

    - `corpus`: Fully qualified url of the corpus that will contain the new
      document.
    - `blob`: The document to be processed.

    The list will only include documents owned by the requesting user, and a
    newly created document will always have the user that sent the `POST` request
    as it's owner.

    As soon as a document is uploaded it will be processed and the results will
    be available as soon as they are ready.
    """
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
    """
    Show details of a specific document and allows the document to be edited.

    `GET` requests will show the document details:

    - `owner`: the user that owns the document.
    - `corpus`: the fully qualified url for the corpus in which this document
      is contained.
    - `size`: the document size (in bytes).
    - `properties`: the url for the list of document properties (the results of
      the analysis will be available in this url when ready).
    - `url`: the fully qualified url for this document.
    - `uploaded_at`: the date this document was uploaded.


    `PUT` requests will edit a document and require:

    - `corpus`: fully qualified url of the corpus that should contain the
      document.
    - `blob`: the document to be processed.

    The owner is set automatically to the requesting user, so it is not
    possible to change the owner using this resource.
    """
    model = Document
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def pre_save(self, obj):
        obj.owner = self.request.user

class PropertyList(generics.RetrieveAPIView):
    """
    Lists all the available analysis results for a document. If a property is
    not listed here, the analysis is either not yet complete or not applicable
    to the specified document.
    """
    serializer_class = PropertyListSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

class PropertyDetail(generics.RetrieveAPIView):
    """
    Shows the result of an analysis for the specified document. The result
    always has one key named `value` and it will contain your result. A list of
    all possible analysis and the corresponding result formats is available in
    our documentation.
    """
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
