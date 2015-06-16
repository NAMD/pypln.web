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
from celery import group
from django.conf import settings
from pypln.backend.workers import *
from pypln.backend.mongodict_adapter import MongoDictAdapter

def call_default_pipeline(doc_id):
    palavras_dependent_tasks = group(
        POS().si(doc_id), Lemmatizer().si(doc_id),
        NounPhrase().si(doc_id), SemanticTagger().si(doc_id)
    )

    (GridFSDataRetriever().si(doc_id) | Extractor().si(doc_id) |
        group(
            (PalavrasRaw().si(doc_id) | palavras_dependent_tasks),
            (Tokenizer().si(doc_id) | FreqDist().si(doc_id) |
                group(Statistics().si(doc_id))
            )
        )
    )()

def create_pipeline_from_document(doc):
    data = {"_id": str(doc.blob.file._id), "id": doc.id}
    create_pipeline(data)

def create_pipeline(data):
    # Add file_id as a property to the document before starting
    # to process it. The first worker will need this property
    document = MongoDictAdapter(doc_id=data['id'],
            host=settings.MONGODB_CONFIG['host'],
            port=settings.MONGODB_CONFIG['port'],
            database=settings.MONGODB_CONFIG['database'])
    document['file_id'] = data['_id']
    call_default_pipeline(data['id'])

def create_indexing_pipeline(doc):
    doc_id = doc.id
    document = MongoDictAdapter(doc_id=doc_id,
            host=settings.MONGODB_CONFIG['host'],
            port=settings.MONGODB_CONFIG['port'],
            database=settings.MONGODB_CONFIG['database'])

    document["file_id"] = str(doc.blob.file._id)
    document["index_name"] = doc.index_name
    document["doc_type"] = doc.doc_type
    (GridFSDataRetriever().si(doc_id) | Extractor().si(doc_id) |
            ElasticIndexer().si(doc_id))()

def get_config_from_router(api, timeout=5):
    client = Client()
    client.connect(api)
    client.send_api_request({'command': 'get configuration'})
    if client.api_poll(timeout):
        result = client.get_api_reply()
    else:
        result = None
    client.disconnect()
    return result
