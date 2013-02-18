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
from collections import Counter
from string import punctuation

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView

from mongodict import MongoDict
from nltk.corpus import stopwords

from apps.core.models import Document
from apps.utils import TAGSET, COMMON_TAGS, LANGUAGES

class VisualizationView(TemplateView):
    """
    Base class for visualization views.  Each visualization should extend this,
    declare it's requirements, label, slug, and a `process' method that returns
    the data necessary in the template context.
    """
    requires = set()
    slug = ''
    label = ''

    @property
    def template_name(self):
        return 'core/visualizations/{}.{}'.format(self.slug, self.kwargs['fmt'])

    # Seriously? Do we really need this?
    # https://docs.djangoproject.com/en/dev/topics/class-based-views/#decorating-the-class
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(VisualizationView, self).dispatch(*args, **kwargs)

    def get_data_from_store(self):
        store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                          port=settings.MONGODB_CONFIG['port'],
                          database=settings.MONGODB_CONFIG['database'],
                          collection=settings.MONGODB_CONFIG['analysis_collection'])

        try:
            properties = set(store['id:{}:_properties'.format(self.document.id)])
        except KeyError:
            # FIXME: We know that we need better information about pipeline
            # status. https://github.com/NAMD/pypln.web/issues/46
            raise Http404("Visualization not found for this document.")

        if not self.requires.issubset(properties):
            # FIXME: We know that we need better information about pipeline
            # status. https://github.com/NAMD/pypln.web/issues/46
            raise Http404("Visualization not ready for this document. "
                    "This means that the necessary processing is not finished "
                    "or that an error has occured.")

        data = {}
        for key in self.requires:
            data[key] = store['id:{}:{}'.format(self.document.id, key)]

        return data

    def process(self):
        return self.get_data_from_store()

    def get_context_data(self, document_slug, fmt):
        self.document = get_object_or_404(Document, slug=document_slug,
                    owner=self.request.user.id)

        context = self.process()
        context['document'] = self.document
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super(VisualizationView, self).render_to_response(
                context, **response_kwargs)

        fmt = self.kwargs['fmt']
        if fmt != "html":
            response["Content-Type"] = "text/{}; charset=utf-8".format('plain'
                    if fmt == 'txt' else fmt)
            response["Content-Disposition"] = ('attachment; '
                    'filename="{}-{}.{}"').format(self.document.slug,
                            self.slug, fmt)
        return response

class PartOfSpeechVisualization(VisualizationView):
    requires = set(['pos', 'tokens', 'tagset'])
    slug = 'part-of-speech'
    label = _('Part-of-speech')

    def warn_about_unknown_tags(self, tag_errors):
        from django.core.mail import mail_admins

        subject = u"Tags not in tagset"
        message = u""
        for item, tagset in tag_errors:
            message += (u"Tag {} was assigned to token \"{}\", but was not found "
                    u"in tagset {}.\n\n").format(item[1], item[0], tagset)
        mail_admins(subject, message)

    def process(self):
        data = self.get_data_from_store()
        pos = []
        token_list = []
        tag_errors = []
        if 'tagset' not in data or data['tagset'] is None:
            tagset = 'en-nltk'
        else:
            tagset = data['tagset']
        if data['pos'] is not None:
            for idx, item in enumerate(data['pos']):
                try:
                    tag = TAGSET[tagset][item[1]]
                    pos.append({'slug': tag['slug'], 'token': item[0]})
                    token_list.append((idx, item[0], item[1]))
                except KeyError:
                    tag_errors.append((item, tagset))

        if tag_errors:
            self.warn_about_unknown_tags(tag_errors)

        return {'pos': pos, 'tagset': TAGSET[tagset], 'most_common': COMMON_TAGS[:20],
                'token_list': token_list}

class PlainTextVisualization(VisualizationView):
    requires = set(['text'])
    slug = 'text'
    label = _('Plain text')

class TokenFrequencyVisualization(VisualizationView):
    requires = set(['freqdist', 'momentum_1', 'momentum_2',
                    'momentum_3', 'momentum_4'])
    slug = 'token-frequency-histogram'
    label = _('Token frequency histogram')

    def process(self):
        data = self.get_data_from_store()

        freqdist = data['freqdist']
        values = Counter()
        for key, value in freqdist:
            values[value] += 1
        data['values'] = [list(x) for x in values.most_common()]
        data['momentum_1'] = '{:.2f}'.format(data['momentum_1'])
        data['momentum_2'] = '{:.2f}'.format(data['momentum_2'])
        data['momentum_3'] = '{:.2f}'.format(data['momentum_3'])
        data['momentum_4'] = '{:.2f}'.format(data['momentum_4'])
        return data

class WordCloudVisualization(VisualizationView):
    requires = set(['freqdist', 'language'])
    slug = 'word-cloud'
    label = _('Word cloud')

    def process(self):
        data = self.get_data_from_store()
        stopwords_list = list(punctuation)
        document_language = LANGUAGES.get(data['language'])
        if document_language and document_language.lower() in stopwords.fileids():
            stopwords_list += stopwords.words(document_language.lower())
        data['freqdist'] = [[x[0], x[1]] for x in data['freqdist'] \
                                                     if x[0] not in stopwords_list]
        return data

class StatisticsVisualization(VisualizationView):
    requires = set(['tokens', 'sentences', 'repertoire',
                    'average_sentence_repertoire',
                    'average_sentence_length'])
    slug = 'statistics'
    label = _('Statistics')

    def process(self):
        data = self.get_data_from_store()
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


available_visualizations = [PlainTextVisualization, PartOfSpeechVisualization,
                            TokenFrequencyVisualization, WordCloudVisualization,
                            StatisticsVisualization]

def visualization_router(*args, **kwargs):
    """
    This view exists only to route the request to the right visualization
    based on the slug.
    """
    slug = kwargs.pop('visualization_slug')
    for view_class in available_visualizations:
        if view_class.slug == slug:
            return view_class.as_view()(*args, **kwargs)
    raise Http404("Visualization {} not found".format(visualization_slug))
