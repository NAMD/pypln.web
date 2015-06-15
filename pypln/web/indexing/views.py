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

from rest_framework import generics
from rest_framework import permissions

from pypln.web.core.models import Document
from pypln.web.core.serializers import DocumentSerializer
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
    - `index_name`: The name of the index inclu
    """
    #model = Document
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, )
