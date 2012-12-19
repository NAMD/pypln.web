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

from django.forms import ModelForm
from core.models import Corpus, Document
from django.forms import FileField
from django.forms.widgets import ClearableFileInput

class CorpusForm(ModelForm):
    class Meta:
        model = Corpus
        fields = ('name', 'description')

class MultipleFileField(FileField):
    widget = ClearableFileInput(attrs={'multiple': 'multiple'})

class DocumentForm(ModelForm):
    blob = MultipleFileField(label="")

    class Meta:
        model = Document
        fields = ('blob', )

    def __init__(self, owner, *args, **kwargs):
        self.owner = owner
        return super(DocumentForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        commit = kwargs.pop('commit', True)
        doc = super(DocumentForm, self).save(*args, commit=False, **kwargs)
        doc.owner = self.owner
        if commit:
            doc.save()
        return doc
