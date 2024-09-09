import re
import uuid
import logging
from datetime import datetime

from django import forms
from django.db.models import Max
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import Course, LearningResource, ScormResource, CourseCategory, Enrollment, Program, Tag, ProgramCourse, Delivery, DeliveryComponent, ProgramCourse
from users.models import Facilitator, Learner
from users.models import User
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


# ============================================================
# ======================= Course Forms =======================
# ============================================================

class CourseForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    prerequisites = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Course
        fields = ['title', 'description', 'short_description', 'category', 'cover_image', 
                  'duration', 'tags', 'prerequisites', 'language', 'difficulty_level']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.TextInput(attrs={'placeholder': 'e.g., English, Spanish'}),
            'difficulty_level': forms.Select(choices=Course.DIFFICULTY_LEVELS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_image'].widget.attrs.update({'class': 'form-control-file'})
        for field in self.fields:
            if field not in ['cover_image', 'tags', 'prerequisites']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class CoursePublishForm(forms.Form):
    confirm_publish = forms.BooleanField(required=True, label="Confirm publish")

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)

    def save(self):
        if self.course and not self.course.is_published:
            self.course.is_published = True
            self.course.save()
        return self.course

class CourseUnpublishForm(forms.Form):
    confirm_unpublish = forms.BooleanField(required=True, label="Confirm unpublish")

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)

    def save(self):
        if self.course and self.course.is_published:
            self.course.is_published = False
            self.course.save()
        return self.course


# ============================================================
# ============= Course Learning Resource Forms ===============
# ============================================================

class LearningResourceForm(forms.ModelForm):
    class Meta:
        model = LearningResource
        fields = ['title', 'description', 'resource_type', 'content', 'external_url', 'order', 'is_mandatory']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False
        self.fields['external_url'].required = False

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        content = cleaned_data.get('content')
        external_url = cleaned_data.get('external_url')

        if resource_type in ['DOCUMENT', 'PRESENTATION', 'VIDEO', 'AUDIO', 'IMAGE'] and not content:
            raise forms.ValidationError("Content file is required for this resource type.")
        elif resource_type == 'LINK' and not external_url:
            raise forms.ValidationError("External URL is required for Link resource type.")

        return cleaned_data
    
class LearningResourceEditForm(forms.ModelForm):
    class Meta:
        model = LearningResource
        fields = ['title', 'description', 'resource_type', 'content', 'external_url', 'order', 'is_mandatory']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False
        self.fields['external_url'].required = False

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        content = cleaned_data.get('content')
        external_url = cleaned_data.get('external_url')

        if resource_type in ['DOCUMENT', 'PRESENTATION', 'VIDEO', 'AUDIO', 'IMAGE'] and not content:
            if not self.instance.content:
                raise forms.ValidationError("Content file is required for this resource type.")
        elif resource_type == 'LINK' and not external_url:
            raise forms.ValidationError("External URL is required for Link resource type.")

        return cleaned_data

class ScormResourceForm(forms.ModelForm):
    class Meta:
        model = ScormResource
        fields = ['scorm_course_id', 'version', 'web_path']

LearningResourceFormSet = inlineformset_factory(
    Course, LearningResource, form=LearningResourceForm,
    extra=1, can_delete=True
)
    

# ============================================================
# ======================= Program Forms ======================
# ============================================================

class ProgramForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    prerequisites = forms.ModelMultipleChoiceField(
        queryset=Program.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Program
        fields = ['title', 'description', 'short_description', 'cover_image', 
                  'program_type', 'duration', 'level', 'provider', 'exam_code', 
                  'exam_link', 'tags', 'prerequisites']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_image'].widget.attrs.update({'class': 'form-control-file'})
        for field in self.fields:
            if field not in ['cover_image', 'tags', 'prerequisites']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})



class ProgramPublishForm(forms.Form):
    confirm_publish = forms.BooleanField(required=True, label="Confirm publish")

    def __init__(self, *args, **kwargs):
        self.program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

    def save(self):
        if self.program and not self.program.is_published:
            self.program.is_published = True
            self.program.save()
        return self.program

class ProgramUnpublishForm(forms.Form):
    confirm_unpublish = forms.BooleanField(required=True, label="Confirm unpublish")

    def __init__(self, *args, **kwargs):
        self.program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

    def save(self):
        if self.program and self.program.is_published:
            self.program.is_published = False
            self.program.save()
        return self.program
    
class ProgramCourseForm(forms.ModelForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    order = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )
    is_mandatory = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    class Meta:
        model = ProgramCourse
        fields = ['course', 'order', 'is_mandatory']

    def __init__(self, *args, **kwargs):
        self.program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.program = self.program
        if commit:
            instance.save()
        return instance
    

# ============================================================
# ======================= Delivery Forms =====================
# ============================================================

class DeliveryCreateForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ['title', 'delivery_type', 'program', 'course', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].queryset = Program.objects.all()
        self.fields['course'].queryset = Course.objects.all()
        self.fields['program'].required = False
        self.fields['course'].required = False

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        program = cleaned_data.get('program')
        course = cleaned_data.get('course')

        if delivery_type == 'PROGRAM':
            if not program:
                self.add_error('program', "Program is required for Program delivery type.")
            if course:
                self.add_error('course', "Course should not be selected for Program delivery type.")
        elif delivery_type == 'COURSE':
            if not course:
                self.add_error('course', "Course is required for Course delivery type.")
            if program:
                self.add_error('program', "Program should not be selected for Course delivery type.")

        return cleaned_data
    
class DeliveryEditForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ['title', 'delivery_type', 'program', 'course', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].queryset = Program.objects.all()
        self.fields['course'].queryset = Course.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        program = cleaned_data.get('program')
        course = cleaned_data.get('course')

        if delivery_type == 'PROGRAM' and not program:
            raise forms.ValidationError("Program delivery must have a program associated.")
        if delivery_type == 'COURSE' and not course:
            raise forms.ValidationError("Course delivery must have a course associated.")

        return cleaned_data

class DeliveryComponentForm(forms.ModelForm):
    class Meta:
        model = DeliveryComponent
        fields = ['delivery', 'is_mandatory', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery'].queryset = Delivery.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        delivery = cleaned_data.get('delivery')
        
        if delivery:
            if delivery.delivery_type == 'PROGRAM':
                if not cleaned_data.get('program_course'):
                    self.add_error('program_course', 'Program course is required for program deliveries.')
            elif delivery.delivery_type == 'COURSE':
                if not cleaned_data.get('learning_resource'):
                    self.add_error('learning_resource', 'Learning resource is required for course deliveries.')
        
        return cleaned_data

class ProgramDeliveryComponentForm(DeliveryComponentForm):
    program_course = forms.ModelChoiceField(queryset=ProgramCourse.objects.all(), required=False)

    class Meta(DeliveryComponentForm.Meta):
        fields = DeliveryComponentForm.Meta.fields + ['program_course']

class CourseDeliveryComponentForm(DeliveryComponentForm):
    learning_resource = forms.ModelChoiceField(queryset=LearningResource.objects.all(), required=False)

    class Meta(DeliveryComponentForm.Meta):
        fields = DeliveryComponentForm.Meta.fields + ['learning_resource']


# ============================================================
# ======================= Enrollment Forms ===================
# ============================================================

class EnrollmentForm(forms.Form):
    ENROLLMENT_TYPES = (
        ('delivery', _('Delivery')),
        ('program', _('Program')),
        ('course', _('Course')),
    )

    enrollment_type = forms.ChoiceField(
        choices=ENROLLMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Enrollment Type")
    )

    delivery = forms.ModelChoiceField(
        queryset=Delivery.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Delivery")
    )

    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Program")
    )

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Course")
    )

    def clean(self):
        cleaned_data = super().clean()
        enrollment_type = cleaned_data.get('enrollment_type')
        delivery = cleaned_data.get('delivery')
        program = cleaned_data.get('program')
        course = cleaned_data.get('course')

        if enrollment_type == 'delivery' and not delivery:
            self.add_error('delivery', _("Please select a delivery for enrollment."))
        elif enrollment_type == 'program' and not program:
            self.add_error('program', _("Please select a program for enrollment."))
        elif enrollment_type == 'course' and not course:
            self.add_error('course', _("Please select a course for enrollment."))

        return cleaned_data
    
class EnrollmentEditForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['status', 'completion_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'completion_date': forms.DateTimeInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'type': 'datetime-local'}),
        }