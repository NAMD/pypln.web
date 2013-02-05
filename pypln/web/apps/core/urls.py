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
from django.conf.urls.defaults import patterns, url
from core.views.visualization import (PartOfSpeechVisualization, PlainTextVisualization,
                                      TokenFrequencyVisualization)


# Visualization urls
urlpatterns = patterns('core.views',
        url(r'^document/(?P<document_slug>.+)/visualization/part-of-speech.(?P<fmt>(html|csv))$',
            PartOfSpeechVisualization.as_view(), name='part_of_speech_visualization'),
        url(r'^document/(?P<document_slug>.+)/visualization/text.(?P<fmt>(html|txt))$',
            PlainTextVisualization.as_view(), name='text_visualization'),
        url(r'^document/(?P<document_slug>.+)/visualization/token-frequency-histogram.(?P<fmt>(html|csv))$',
            TokenFrequencyVisualization.as_view(), name='token_frequency_histogram_visualization'),
        url(r'^document/(?P<document_slug>.+)/visualization/(?P<visualization>[-\w]+).(?P<fmt>(html|csv|txt))$',
            'document_visualization', name='document_visualization'),
)

urlpatterns += patterns('core.views',
        url(r'^corpora/?$', 'corpora_list', name='corpora_list'),
        url(r'^corpora/(?P<corpus_slug>.+)/?$', 'corpus_page',
            name='corpus_page'),
        url(r'^documents/?$', 'document_list', name='document_list'),
        url(r'^document/(?P<document_slug>.+)/download$', 'document_download',
            name='document_download'),
        url(r'^document/(?P<document_slug>.+)/?$', 'document_page',
            name='document_page'),
        url(r'^search', 'search', name='search'),
)
