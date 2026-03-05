from django import forms
from .models import ForensicRequest
from .utils import get_available_models


class ForensicRequestForm(forms.ModelForm):
    selected_models = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = ForensicRequest
        fields = ['input_file']
        widgets = {
            'input_file': forms.FileInput(attrs={
                # ✅ Accept both images and videos
                'accept': 'video/*,image/*',
                'class': 'hidden',
            })
        }

    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)

        # Set model choices based on user permissions
        available_models = get_available_models(is_admin=is_admin)
        self.fields['selected_models'].choices = [(m, m) for m in available_models]

        if not is_admin:
            self.fields['selected_models'].initial = available_models

        self.is_admin = is_admin

    def clean_input_file(self):
        file = self.cleaned_data.get('input_file')

        if file:
            content_type = file.content_type

            # ✅ Allow video OR image
            if not (
                content_type.startswith('video/') or 
                content_type.startswith('image/')
            ):
                raise forms.ValidationError(
                    "Please upload a valid video or image file."
                )

            # Optional: Separate size limits
            max_video_size = 1024 * 1024 * 1024  # 1GB
            max_image_size = 20 * 1024 * 1024    # 20MB

            if content_type.startswith('video/') and file.size > max_video_size:
                raise forms.ValidationError(
                    "Video file size must be less than 1GB."
                )

            if content_type.startswith('image/') and file.size > max_image_size:
                raise forms.ValidationError(
                    "Image file size must be less than 20MB."
                )

        return file