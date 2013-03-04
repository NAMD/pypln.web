#!/usr/bin/env python
# coding: utf-8

import os
import sys
import time

from logging import Logger, StreamHandler, Formatter

from pypln.api import PyPLN


def main():
    # Configuration of the benchmark
    pypln_version = sys.argv[1]
    number_of_documents = 1000
    pypln_url = 'http://localhost:8000'
    username, password = 'admin', 'admin'
    corpus_name = 'Test Call Duration Corpus'
    corpus_slug = corpus_name.lower().replace(' ', '-')
    corpus_description = ('Testing `PyPLN.add_document` call duration for '
                          'PyPLN version {} ({} documents)')\
                          .format(pypln_version, number_of_documents)

    # Configuring logger
    logger = Logger('Benchmark-add_document-{}'.format(pypln_version))
    handler = StreamHandler(sys.stdout)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - '
                          '%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info('Logging in...')
    pypln = PyPLN(pypln_url)
    pypln.login(username, password)

    logger.info('Retrieving (or adding, if needed) desired corpus...')
    corpora = pypln.corpora()
    try:
        corpus = [c for c in corpora if c.slug == corpus_slug][0]
    except IndexError:
        corpus = pypln.add_corpus(corpus_name, corpus_description)
    # There's a bug in pypln.api, so we should set corpus url manually:
    corpus.url = '{}/corpora/{}'.format(pypln_url, corpus_slug)

    logger.info('Adding documents...')
    data_filename = 'benchmark-add_document-{}-{}.dat'\
                    .format(number_of_documents, pypln_version)
    data = open(data_filename, 'w')
    for index in xrange(number_of_documents):
        filename = 'test-{}.txt'.format(index)
        file_path = '/tmp/' + filename
        with open(file_path, 'w') as fp:
            fp.write('This is a test.\nTest number: {}.\n'.format(index))
        with open(file_path, 'r') as fp:
            start_time = time.time()
            corpus.add_document(fp, filename)
            end_time = time.time()
            delta_time = end_time - start_time
            data.write('{}\t{}\n'.format(index, delta_time))
            data.flush()
            logger.info('  Added {}'.format(filename))
        os.unlink(file_path)
    data.close()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Error! Usage: {} <pypln_version>'.format(sys.argv[0])
        exit(1)
    main()
