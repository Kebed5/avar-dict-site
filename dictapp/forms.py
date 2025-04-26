from django import forms
from .models import SuggestedEntry

class SuggestedEntryForm(forms.ModelForm):
    class Meta:
        model = SuggestedEntry
        fields = ['avar_word', 'russian_translations', 'english_translations', 'examples']

from .models import AudioEntry

class AudioEntryForm(forms.ModelForm):
    class Meta:
        model = AudioEntry
        fields = ['entry', 'audio_file']
