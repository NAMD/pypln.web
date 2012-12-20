#!/usr/bin/env python
# coding: utf-8

import os

from django.core.management.base import BaseCommand
from mongodict import MongoDict

from pypln.web.apps.core.models import Document, index_schema
from pypln.web.apps.core.search import WhooshIndex


def process_running(pid):
    '''Check for the existence of a process ID'''
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def clone_of_me_running(pid_filename):
    result = False
    if os.path.exists(pid_filename):
        with open(pid_filename) as pid_file:
            try:
                pid = int(pid_file.read().strip())
            except ValueError:
                pass
            else:
                if process_running(pid):
                    result = True
    return result

def write_pid_file(filename):
    with open(filename, 'w') as pid_file:
        my_pid = os.getpid()
        pid_file.write('{}\n'.format(my_pid))

class Command(BaseCommand):
    args = ''
    help = 'Update the index with new documents'
    can_import_settings = True

    def handle(self, *args, **kwargs):
        from django.conf import settings


        if clone_of_me_running(pid_filename=settings.INDEX_RUNNING):
            self.stdout.write('Another indexing process is running. Exiting.\n')
        else:
            write_pid_file(filename=settings.INDEX_RUNNING)

            not_indexed_count = Document.objects.filter(indexed=False).count()
            if not_indexed_count:
                self.stdout.write('Documents to be indexed: {}\n'\
                                  .format(not_indexed_count))
                index = WhooshIndex(settings.INDEX_PATH, index_schema)
                store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                                  port=settings.MONGODB_CONFIG['port'],
                                  database=settings.MONGODB_CONFIG['database'],
                                  collection=settings.MONGODB_CONFIG['analysis_collection'])

                not_indexed_documents = Document.objects.filter(indexed=False)
                for document in not_indexed_documents:
                    document_key = 'id:{}:'.format(document.id)
                    if document_key + '_properties' in store and \
                       'text' in store[document_key + '_properties']:
                        text = store[document_key + 'text']
                        index.add_document(id=unicode(document.id),
                                           filename=document.slug,
                                           content=text)
                        document.indexed = True
                        document.save()
                        self.stdout.write('  Indexed id={}, filename={}\n'\
                                          .format(document.id, document.slug))
                    else:
                        self.stdout.write('  Not indexed (text not ready) '
                                          'id={}, filename={}\n'\
                                          .format(document.id, document.slug))

            else:
                self.stdout.write('All documents are already indexed.\n')

            os.unlink(settings.INDEX_RUNNING)
