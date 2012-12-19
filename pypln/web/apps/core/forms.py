from django.forms import ModelForm
from core.models import Corpus, Document

class CorpusForm(ModelForm):
    class Meta:
        model = Corpus
        fields = ('name', 'description')

class DocumentForm(ModelForm):
    class Meta:
        model = Document
        fields = ('blob', )
