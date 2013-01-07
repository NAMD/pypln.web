#!/usr/bin/env python
# coding: utf-8

import os

from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser


class WhooshIndex(object):
    '''Integrate whoosh's indexer and searcher'''

    def __init__(self, index_path, schema=None):
        '''Initialize a WhooshIndex based on path `index_path`

        If it's the first time you instantiate this class for `index_path`,
        it'll create the directory and needs a schema to create index metadata.
        '''
        if not os.path.exists(index_path):
            if schema is None:
                raise ValueError('You need to specify a `schema` when creating'
                                 ' an index')
            os.mkdir(index_path)
            self._index = create_in(index_path, schema)
            self._schema = schema
        else:
            self._index = open_dir(index_path)
            self._schema = self._index.schema

    def add_document(self, **document):
        '''Add a document to the index.

        Document properties should be passed as parameters, like in:

        >>> my_index.add_document(title=u'My Title', content=u'The content')
        '''
        writer = self._index.writer()
        writer.add_document(**document)
        writer.commit()

    def add_documents(self, documents):
        '''Add a list of documents (`list` of `dict`s) to the index

        It's an optimized version of `add_document` since it calls `commit`
        only in the end.
        '''
        writer = self._index.writer()
        for document in documents:
            writer.add_document(**document)
        writer.commit()

    def search(self, query, field):
        '''Perform a search in the field `field` in indexed documents'''
        query_object = QueryParser(field, self._schema).parse(query)
        searcher = self._index.searcher()
        results = searcher.search(query_object)
        return results
