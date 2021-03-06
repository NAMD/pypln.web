# -*- coding:utf-8 -*-
#
# Copyright 2015 NAMD-EMAP-FGV
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
# along with PyPLN.  If not, see <https://www.gnu.org/licenses/>.
import elasticsearch

from django.conf import settings

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from pypln.web.core.models import Document
from pypln.web.core.serializers import IndexedDocumentSerializer
from pypln.web.indexing.serializers import QuerySerializer
from pypln.web.backend_adapter.pipelines import create_indexing_pipeline


class IndexDocument(generics.CreateAPIView):
    """
    Create a new Document and runs the backend workers necessary to index it in
    elasticsearch. The index will be accessible by the index querying endpoint
    of this API.

    `POST` requests will create and index a new document using the indexing
    pipeline. They should include:

    - `corpus`: Fully qualified url of the corpus that will contain the new
      document.
    - `blob`: The document to be processed.
    - `doc_type`: The type of the document (to be passed on to elastic)
    - `index_name`: The name of the index. If the name does not start with your
      username, it will be automatically prefixed to include it.
    """
    serializer_class = IndexedDocumentSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def perform_create(self, serializer):
        username = self.request.user.username
        provided_index_name = serializer.validated_data['index_name']

        if not provided_index_name.startswith(username):
            provided_index_name = "{}_{}".format(username, provided_index_name)

        instance = serializer.save(owner=self.request.user,
                index_name=provided_index_name)
        create_indexing_pipeline(instance)

class IndexQuery(APIView):
    """
    Query an existing index using the Elastic DSL.

    `GET` requests will query the index and return the results.  They should
    include:

    - `index_name`: The name of the index to be queried.
    - `q`: The query itself.
    """
    # - `sort`:
    # - `size`:

    permission_classes = (permissions.IsAuthenticated, )

    ES = elasticsearch.Elasticsearch(hosts=settings.ELASTICSEARCH_CONFIG['hosts'])

    def get(self, request, format=None):
        serializer = QuerySerializer(data=request.query_params,
                context={"request": self.request})
        serializer.is_valid(raise_exception=True)
        try:
            results = self.ES.search(
                index=serializer.validated_data["index_name"],
                q=serializer.validated_data["q"],
            )
        except elasticsearch.NotFoundError:
            index_document_url = reverse("index-document")
            INDEX_NAME_ERROR_MSG = ("The index you looked for was not found. "
                            "Remember stored index names are always prefixed with your "
                            "username. See the documentation in {} for "
                            "details".format(index_document_url))
            raise NotFound(detail=INDEX_NAME_ERROR_MSG)

        return Response(data=results["hits"])
