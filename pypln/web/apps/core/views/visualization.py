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
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from mongodict import MongoDict

from apps.core.models import Document
from apps.utils import TAGSET, COMMON_TAGS

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
    requires = set(['pos', 'tokens'])
    slug = 'part-of-speech'
    label = _('Part-of-speech')

    def warn_about_unknown_tags(self, tag_errors):
        from django.core.mail import mail_admins

        subject = "Tags not in tagset"
        message = ""
        for item in tag_errors:
            message += ("Tag {} was assigned to token \"{}\", but was not found "
                    "in tagset.\n\n").format(item[1], item[0])
        mail_admins(subject, message)

    def process(self):
        data = self.get_data_from_store()
        pos = []
        token_list = []
        tag_errors = []

        if data['pos'] is not None:
            for idx, item in enumerate(data['pos']):
                try:
                    tag = TAGSET[item[1]]
                    pos.append({'slug': tag['slug'], 'token': item[0]})
                    token_list.append((idx, item[0], item[1]))
                except KeyError:
                    tag_errors.append(item)

        if tag_errors:
            self.warn_about_unknown_tags(tag_errors)

        return {'pos': pos, 'tagset': TAGSET, 'most_common': COMMON_TAGS[:20],
                'token_list': token_list}

available_visualizations = [PartOfSpeechVisualization]
