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

from django.forms import ModelForm, FileField, ValidationError
from django.forms.models import save_instance
from core.models import Corpus, Document
from django.forms.widgets import ClearableFileInput
from django.utils.translation import ugettext as _

class CorpusForm(ModelForm):
    class Meta:
        model = Corpus
        fields = ('name', 'description')

class MultipleFileField(FileField):
    widget = ClearableFileInput(attrs={'multiple': 'multiple'})

class DocumentForm(ModelForm):
    """
    This is not fully compatible with ModelForm, so expect
    differences. But the point is to be able to deal with more than
    one file uploaded.
    """
    blob = MultipleFileField(label="")

    class Meta:
        model = Document
        fields = ('blob', )

    def __init__(self, owner, *args, **kwargs):
        self.owner = owner
        return super(DocumentForm, self).__init__(*args, **kwargs)

    def clean_blob(self):
        blob = self.cleaned_data['blob']
        if len(blob.name) >= 100:
            raise ValidationError(_("File names need to be shorter than 100 "
                                    "characters."))
        return blob

    def save(self, *args, **kwargs):
        commit = kwargs.pop('commit', True)
        instances = []
        if self.errors:
            raise ValueError("Could not save documents because form data didn't validate.")

        for f in self.files.getlist('blob'):
            doc = Document(owner=self.owner, blob=f)
            instances.append(save_instance(self, doc, commit=commit,
                                           construct=False))

        return instances
