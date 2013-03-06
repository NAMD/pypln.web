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

    def __init__(self, *args, **kwargs):
        user = kwargs['context']['request'].user
        self.base_fields['corpus'].queryset = Corpus.objects.filter(owner=user)
        super(DocumentSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Document
