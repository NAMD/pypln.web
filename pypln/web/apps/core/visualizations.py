# coding: utf-8
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

from string import punctuation
from django.utils.translation import ugettext as _
from nltk.corpus import stopwords
from utils import LANGUAGES


def _statistics(data):
    data['repertoire'] = '{:.2f}'.format(data['repertoire'] * 100)
    data['average_sentence_repertoire'] = \
            '{:.2f}'.format(data['average_sentence_repertoire'] * 100)
    data['average_sentence_length'] = '{:.2f}'.format(data['average_sentence_length'])
    data['number_of_tokens'] = len(data['tokens'])
    data['number_of_unique_tokens'] = len(set(data['tokens']))
    sentences = []
    for sentence in data['sentences']:
        sentences.append(' '.join(sentence))
    data['number_of_sentences'] = len(sentences)
    data['number_of_unique_sentences'] = len(set(sentences))
    data['percentual_tokens'] = '{:.2f}'.format(100 * data['number_of_unique_tokens'] / data['number_of_tokens'])
    data['percentual_sentences'] = '{:.2f}'.format(100 * data['number_of_unique_sentences'] / data['number_of_sentences'])
    return data

def _wordcloud(data):
    stopwords_list = list(punctuation)
    document_language = LANGUAGES.get(data['language'])
    if document_language and document_language.lower() in stopwords.fileids():
        stopwords_list += stopwords.words(document_language.lower())
    data['freqdist'] = [[x[0], x[1]] for x in data['freqdist'] \
                                                 if x[0] not in stopwords_list]
    return data

VISUALIZATIONS = {
        'statistics': {
            'label': _('Statistics'),
            'requires': set(['tokens', 'sentences', 'repertoire',
                             'average_sentence_repertoire',
                             'average_sentence_length']),
            'process': _statistics,
        },
        'word-cloud': {
            'label': _('Word cloud'),
            'requires': set(['freqdist', 'language']),
            'process': _wordcloud,
        },
}
