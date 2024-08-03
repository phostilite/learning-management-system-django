import re
import uuid
import logging
from datetime import datetime

from django import forms
from django.db.models import Max
from django.forms import inlineformset_factory

from .models import Course, CourseDelivery, LearningResource, ScormResource, CourseCategory
from users.models import Facilitator, Learner

logger = logging.getLogger(__name__)

class CourseBasicInfoForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'short_description', 'category', 'cover_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super(CourseBasicInfoForm, self).__init__(*args, **kwargs)
        self.fields['category'].choices = [(category.id, category.name) for category in CourseCategory.objects.all()]

class LearningResourceForm(forms.ModelForm):
    resource_type = forms.ChoiceField(choices=LearningResource.RESOURCE_TYPES, widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = LearningResource
        fields = ['title', 'description', 'resource_type', 'content', 'external_url', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        content = cleaned_data.get('content')
        external_url = cleaned_data.get('external_url')

        if resource_type in ['VIDEO', 'DOCUMENT', 'PRESENTATION', 'SCORM'] and not content:
            raise forms.ValidationError(f"Please upload a file for {resource_type} resource type.")
        elif resource_type == 'LINK' and not external_url:
            raise forms.ValidationError("Please provide an external URL for this resource type.")

        if resource_type == 'SCORM':
            # Generate a unique SCORM course ID
            scorm_course_id = f"COURSE-{uuid.uuid4().hex[:6].upper()}"
            scorm_version = "1"
            cleaned_data['scorm_details'] = {
                'scorm_course_id': scorm_course_id,
                'version': scorm_version
            }

        return cleaned_data

class ScormResourceForm(forms.ModelForm):
    class Meta:
        model = ScormResource
        fields = ['scorm_course_id', 'version', 'web_path']

LearningResourceFormSet = inlineformset_factory(
    Course, LearningResource, form=LearningResourceForm,
    extra=1, can_delete=True
)