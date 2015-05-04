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
from django.conf import settings
from pypelinin import Job, Pipeline, PipelineManager, Client
from pypln.backend.workers import GridFSDataRetriever, Extractor
from pypln.backend.mongodict_adapter import MongoDictAdapter

default_pipeline = {
    Job("Extractor"): (Job("PalavrasRaw"), Job("Tokenizer")),
    Job("PalavrasRaw"): (Job("POS"),
                         Job("Lemmatizer"), Job("NounPhrase"),
                         Job("SemanticTagger")),
    Job("Tokenizer"): Job("FreqDist"),
    Job("FreqDist"): (Job("Statistics"), Job("WordCloud")),
}

def create_pipeline(data):
    # Add file_id as a property to the document before starting
    # to process it. The first worker will need this property
    document = MongoDictAdapter(doc_id=data['id'],
            database=settings.MONGODB_CONFIG['database'])
    document['file_id'] = data['_id']
    (GridFSDataRetriever().si(data['id']) | Extractor().si(data['id']))()


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
