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
from bson import ObjectId
from celery import group
from django.conf import settings
from pypln.backend.workers import *
from pypln.web.core.models import mongodb_storage

def call_default_pipeline(doc_id):
    palavras_dependent_tasks = group(
        POS().si(doc_id), Lemmatizer().si(doc_id),
        NounPhrase().si(doc_id), SemanticTagger().si(doc_id)
    )

    (Extractor().si(doc_id) | Tokenizer().si(doc_id) |
        group(
            (PalavrasRaw().si(doc_id) | palavras_dependent_tasks),
            (FreqDist().si(doc_id) | group(Statistics().si(doc_id)))
        )
    )()

def create_pipeline_from_document(doc):
    call_default_pipeline(ObjectId(doc.blob.name))

def create_indexing_pipeline(doc):
    doc_id = ObjectId(doc.blob.name)
    mongodb_storage.collection.update({'_id': doc_id}, {"$set":
            {"index_name": doc.index_name, "doc_type": doc.doc_type}})
    (Extractor().si(doc_id) | ElasticIndexer().si(doc_id))()

def corpus_freqdist(corpus):
    blob_ids = map(ObjectId, corpus.document_set.values_list('blob', flat=True))
    CorpusFreqDist().delay(corpus.pk, blob_ids)

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
