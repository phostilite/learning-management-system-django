import re
import uuid
import logging
from datetime import datetime

from django import forms
from django.db.models import Max
from django.forms import inlineformset_factory

from .models import Course, CourseDelivery, LearningResource, ScormResource, CourseCategory, Enrollment
from users.models import Facilitator, Learner
from users.models import User
from django.contrib.auth.models import Group

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

class CourseDeliveryForm(forms.ModelForm):
    facilitators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = CourseDelivery
        fields = ['title', 'delivery_code', 'delivery_type', 'enrollment_type', 
                  'facilitators', 'start_date', 'end_date', 'max_participants', 
                  'is_mandatory', 'status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.course = self.course
        if commit:
            instance.save()
            self.save_m2m()
        return instance
    
class EnrollmentForm(forms.Form):
    learners = forms.ModelMultipleChoiceField(
        queryset=Learner.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Learners to Enroll"
    )

    def __init__(self, *args, **kwargs):
        self.course_delivery = kwargs.pop('course_delivery', None)
        super().__init__(*args, **kwargs)
        
        # Get the learner group
        learner_group = Group.objects.get(name='learner')
        
        # Filter learners who are in the learner group and not already enrolled
        enrolled_user_ids = Enrollment.objects.filter(course_delivery=self.course_delivery).values_list('user_id', flat=True)
        self.fields['learners'].queryset = Learner.objects.filter(
            user__groups=learner_group
        ).exclude(
            user__id__in=enrolled_user_ids
        )

    def clean_learners(self):
        learners = self.cleaned_data['learners']
        if not learners:
            raise forms.ValidationError("Please select at least one learner to enroll.")
        return learners

    def save(self):
        learners = self.cleaned_data['learners']
        enrollments = []
        for learner in learners:
            enrollment, created = Enrollment.objects.get_or_create(
                user=learner.user,
                course_delivery=self.course_delivery,
                defaults={'status': 'ENROLLED'}
            )
            if created:
                enrollments.append(enrollment)
        return enrollments