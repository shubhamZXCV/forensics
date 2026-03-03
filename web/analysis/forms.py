from django import forms
from .models import ForensicRequest
from .utils import get_available_models

class ForensicRequestForm(forms.ModelForm):
    models_choices = [(m, m) for m in get_available_models()]
    selected_models = forms.MultipleChoiceField(
        choices=models_choices, 
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = ForensicRequest
        fields = ['input_file', 'media_type', 'selected_models']

    def clean_input_file(self):
        import os
        file = self.cleaned_data.get('input_file', False)
        if file:
            app_version = os.environ.get('APP_VERSION', 'v1')
            if app_version == 'v2':
                if not file.content_type.startswith('video/'):
                    raise forms.ValidationError(f"{app_version} only supports video files. Please upload a valid video.")
        return file
