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

import datetime
import json

from mimetypes import guess_type

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.defaultfilters import slugify, pluralize
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse

from core.models import Corpus, Document, index_schema
from core.forms import CorpusForm, DocumentForm
from django.conf import settings
from apps.core.visualizations import VISUALIZATIONS, pos_highlighter

from utils import LANGUAGES, create_pipelines
from mongodict import MongoDict

from pypln.web.apps.core.search import WhooshIndex
from pypln.web.apps.core.visualizations import VISUALIZATIONS
from pypln.web.apps.utils import LANGUAGES, create_pipelines


def _search_filtering_by_owner(index, query, owner, corpus=None):
    if corpus is not None:
        permitted_documents = Document.objects.filter(owner=owner,
                                                      corpus=corpus)
    else:
        permitted_documents = Document.objects.filter(owner=owner)
    permitted_documents_by_id = {doc.id: doc for doc in permitted_documents}
    permitted_ids = [doc.id for doc in permitted_documents]

    found_documents = index.search(query, 'content')
    found_documents_by_id = {int(doc[u'id']): doc for doc in found_documents}
    found_ids = found_documents_by_id.keys()

    result_ids = set(permitted_ids).intersection(set(found_ids))
    results = []
    for document_id in permitted_ids:
        if document_id in result_ids:
            found_document = found_documents_by_id[document_id]
            document = permitted_documents_by_id[document_id]
            document.concordance = found_document.highlights('content')
            results.append(document)
    return results

def index(request):
    return render_to_response('core/homepage.html', {},
            context_instance=RequestContext(request))

@login_required
def corpora_list(request, as_json=False):
    #TODO: this view needs an urgent refactoring. This is code is really
    # confusing and there are a lot of duplications. We should do as we did
    # with the document upload process, and try to move functionality to the
    # form.
    if request.method == 'POST':
        form = CorpusForm(request.POST)
        if not form.is_valid():
            request.user.message_set.create(message=_('ERROR: all fields are '
                                                      'required!'))
        else:
            new_corpus = form.save(commit=False)
            new_corpus.slug = slugify(new_corpus.name)
            new_corpus.owner = request.user
            new_corpus.date_created = datetime.datetime.now()
            new_corpus.last_modified = datetime.datetime.now()
            try:
                new_corpus.validate_unique()
            except ValidationError as exc:
                messages.error(request, exc.message_dict['__all__'][0])
                data = {'corpora': Corpus.objects.filter(owner=request.user.id),
                        'form': form}
                return render_to_response('core/corpora.html', data,
                        context_instance=RequestContext(request))

            new_corpus.save()
            request.user.message_set.create(message=_('Corpus created '
                                                      'successfully!'))
            return HttpResponseRedirect(reverse('corpora_list'))
    else:
        form = CorpusForm()

    data = {'corpora': Corpus.objects.filter(owner=request.user.id),
            'form': form}
    return render_to_response('core/corpora.html', data,
            context_instance=RequestContext(request))

@login_required
def upload_documents(request, corpus_slug):
    #TODO: accept (and uncompress) .tar.gz and .zip files
    #TODO: enforce document type
    corpus = get_object_or_404(Corpus, slug=corpus_slug, owner=request.user.id)
    form = DocumentForm(request.user, request.POST, request.FILES)
    if form.is_valid():
        docs = form.save(commit=False)
        pipelines_data = []
        for doc in docs:
            doc.save()
            # XXX: updating the corpus_set should probably be done in
            # the model, but we'll keep it here since the model might
            # change a bit, and maybe take care of this in a better
            # way.
            doc.corpus_set.add(corpus)
            for corpus in doc.corpus_set.all():
                corpus.last_modified = datetime.datetime.now()
                corpus.save()
            pipelines_data.append({'_id': str(doc.blob.file._id), 'id': doc.id})

        create_pipelines(settings.ROUTER_API, settings.ROUTER_BROADCAST,
                    pipelines_data, timeout=settings.ROUTER_TIMEOUT)
        number_of_uploaded_docs = len(docs)
        # I know I should be using string.format, but gettext doesn't support
        # it yet: https://savannah.gnu.org/bugs/?30854
        message = ungettext('%(count)s document uploaded successfully!',
                '%(count)s documents uploaded successfully!',
                number_of_uploaded_docs) % {'count': number_of_uploaded_docs}
        messages.info(request, message)
        return HttpResponseRedirect(reverse('corpus_page',
                                            kwargs={'corpus_slug': corpus_slug}))
    else:
        data = {'corpus': corpus, 'form': form}
        return render_to_response('core/corpus.html', data,
                                  context_instance=RequestContext(request))

@login_required
def list_corpus_documents(request, corpus_slug):
    corpus = get_object_or_404(Corpus, slug=corpus_slug, owner=request.user.id)
    form = DocumentForm(request.user)
    data = {'corpus': corpus, 'form': form}
    return render_to_response('core/corpus.html', data,
            context_instance=RequestContext(request))

@login_required
def corpus_page(request, corpus_slug):
    if request.method == 'POST':
        return upload_documents(request, corpus_slug)
    else:
        return list_corpus_documents(request, corpus_slug)

@login_required
def document_page(request, document_slug):
    try:
        document = Document.objects.get(slug=document_slug,
                owner=request.user.id)
    except ObjectDoesNotExist:
        return render_to_response('core/404.html', {},
                context_instance=RequestContext(request))

    data = {'document': document,
            'corpora': Corpus.objects.filter(owner=request.user.id)}
    store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                      port=settings.MONGODB_CONFIG['port'],
                      database=settings.MONGODB_CONFIG['database'],
                      collection=settings.MONGODB_CONFIG['analysis_collection'])
    properties = set(store.get('id:{}:_properties'.format(document.id), []))
    metadata = store.get('id:{}:file_metadata'.format(document.id), {})
    language = store.get('id:{}:language'.format(document.id), None)
    metadata['language'] = LANGUAGES[language] if language else _('Unknown')
    data['metadata'] = metadata
    visualizations = []
    for key, value in VISUALIZATIONS.items():
        if value['requires'].issubset(properties):
            visualizations.append({'slug': key, 'label': value['label']})
    data['visualizations'] = visualizations
    return render_to_response('core/document.html', data,
        context_instance=RequestContext(request))

def document_visualization(request, document_slug, visualization, fmt):
    try:
        document = Document.objects.get(slug=document_slug,
                owner=request.user.id)
    except ObjectDoesNotExist:
        return HttpResponse('Document not found', status=404)

    data = {}
    store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                      port=settings.MONGODB_CONFIG['port'],
                      database=settings.MONGODB_CONFIG['database'],
                      collection=settings.MONGODB_CONFIG['analysis_collection'])

    try:
        properties = set(store['id:{}:_properties'.format(document.id)])
    except KeyError:
        return HttpResponse('Visualization not found', status=404)
    if visualization not in VISUALIZATIONS or \
            not VISUALIZATIONS[visualization]['requires'].issubset(properties):
        return HttpResponse('Visualization not found', status=404)

    data = {}
    for key in VISUALIZATIONS[visualization]['requires']:
        data[key] = store['id:{}:{}'.format(document.id, key)]
    template_name = 'core/visualizations/{}.{}'.format(visualization, fmt)
    try:
        template = get_template(template_name)
    except TemplateDoesNotExist:
        raise Http404("Visualization is not available in this format.")
    if 'process' in VISUALIZATIONS[visualization]:
        data = VISUALIZATIONS[visualization]['process'](data)
    data['document'] = document
    response = render_to_response(template_name, data,
            context_instance=RequestContext(request))
    if fmt != "html":
        response["Content-Type"] = "text/{}; charset=utf-8".format(fmt)
        response["Content-Disposition"] = 'attachment; filename="{}-{}.{}"'.format(document.slug, visualization, fmt)
    return response

@login_required
def document_list(request):
    data = {'documents': Document.objects.filter(owner=request.user.id)}
    return render_to_response('core/documents.html', data,
            context_instance=RequestContext(request))

@login_required
def document_download(request, document_slug):
    try:
        document = Document.objects.get(slug=document_slug,
                owner=request.user.id)
    except ObjectDoesNotExist:
        return render_to_response('core/404.html', {},
                context_instance=RequestContext(request))
    filename = document.blob.name.split('/')[-1]
    file_mime_type = guess_type(filename)[0]
    response = HttpResponse(document.blob, content_type=file_mime_type)
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    return response

@login_required
def search(request):
    query = request.GET.get('query', '').strip()
    data = {'results': [], 'query': query}
    corpus_slug = request.GET.get('corpus', '').strip()
    corpus = None
    if corpus_slug:
        corpus = Corpus.objects.filter(slug=corpus_slug)[0]
        data['corpus'] = corpus
    if query:
        index = WhooshIndex(settings.INDEX_PATH, index_schema)
        data['results'] = _search_filtering_by_owner(index=index, query=query,
                                                     owner=request.user,
                                                     corpus=corpus)
    return render_to_response('core/search.html', data,
                              context_instance=RequestContext(request))
