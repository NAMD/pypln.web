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
from django.forms.models import ModelChoiceIterator
from rest_framework import serializers
from rest_framework.reverse import reverse

from pypln.web.core.models import Corpus, Document

class CorpusSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.Field(source="owner.username")
    documents = serializers.HyperlinkedRelatedField(many=True, read_only=True,
            source='document_set.all', view_name="document-detail")
    class Meta:
        model = Corpus

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.Field(source="owner.username")
    corpus = serializers.HyperlinkedRelatedField(view_name="corpus-detail")
    size = serializers.Field(source="blob.size")
    properties = serializers.HyperlinkedIdentityField(view_name="property-list")

    def __init__(self, *args, **kwargs):
        # If the serializer is treating input from a view, there will be a
        # context from which we can take the owner, and filter the possible
        # corpora with it.
        if 'context' in kwargs:
            user = kwargs['context']['request'].user
            self.base_fields['corpus'].queryset = Corpus.objects.filter(owner=user)
        # If we get a document that already exists, we can filter based on it's
        # owner.
        elif args:
            document = args[0]
            self.base_fields['corpus'].queryset = Corpus.objects.filter(
                    owner=document.owner)
        # In other cases we don't filter the queryset. All the user input
        # should come through a view, and this view needs to send us a
        # 'context' and if we do create a document, we should set its owner
        # anyway. This means our Serializer needs to have either a context or a
        # document.
        else:
            raise ValueError("DocumentSerializer needs either a Document or a "
                    "context.")
        super(DocumentSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Document

class PropertyListSerializer(serializers.Serializer):
    properties = serializers.SerializerMethodField("get_property_urls")

    def get_property_urls(self, obj):
        request = self.context['request']
        try:
            return [reverse('property-detail', kwargs={"pk": obj.id,
                "property": prop}, request=request) for prop
                in obj.properties.keys()]
        except KeyError:
            return []
