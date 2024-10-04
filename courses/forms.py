# Standard library imports
import re
import uuid
import logging
from datetime import datetime

# Django imports
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

# Third-party imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML, Fieldset, Field
from crispy_forms.bootstrap import TabHolder, Tab
from crispy_forms.bootstrap import PrependedText

# Local application imports
from .models import (
    Course, LearningResource, ScormResource, CourseCategory, Enrollment, 
    Program, Tag, ProgramCourse, Delivery, DeliveryComponent, DeliveryInstructor    
)
from users.models import User
from courses.models import Delivery, Program, Course, User

# Get the user model
User = get_user_model()

# Set up logging
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
    content = forms.FileField(required=False)
    scorm_file = forms.FileField(required=False)
    scorm_version = forms.CharField(max_length=50, required=False)

    class Meta:
        model = LearningResource
        fields = ['title', 'description', 'resource_type', 'content', 'external_url', 'order', 'is_mandatory']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['external_url'].required = False
        self.fields['content'].required = False

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        content = cleaned_data.get('content')
        external_url = cleaned_data.get('external_url')
        scorm_file = cleaned_data.get('scorm_file')
        scorm_version = cleaned_data.get('scorm_version')

        if resource_type == 'LINK' and not external_url:
            raise forms.ValidationError("External URL is required for Link resource type.")
        elif resource_type == 'SCORM':
            if not scorm_file:
                raise forms.ValidationError("SCORM file is required for SCORM resource type.")
            if not scorm_version:
                raise forms.ValidationError("SCORM version is required for SCORM resource type.")
        elif resource_type in ['VIDEO', 'DOCUMENT'] and not content:
            raise forms.ValidationError(f"{resource_type.capitalize()} file is required for {resource_type} resource type.")

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
    instructors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='facilitator'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Select one or more instructors for this delivery.")
    )

    class Meta:
        model = Delivery
        fields = [
            'title', 'description', 'delivery_type', 'delivery_mode', 
            'program', 'course', 'instructors',
            'start_date', 'end_date', 'enrollment_start',
            'enrollment_end', 'deactivation_date', 'max_participants',
            'is_active', 'is_mandatory', 'completion_criteria', 'minimum_score',
            'attendance_threshold', 'issue_certificate', 'allow_self_unenroll'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'enrollment_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'enrollment_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'deactivation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields['program'].queryset = Program.objects.filter(is_published=True)
        self.fields['course'].queryset = Course.objects.filter(is_published=True)

        # Add helper text to each field
        self.fields['title'].help_text = _("Enter a descriptive title for this delivery.")
        self.fields['description'].help_text = _("Provide a detailed description of the delivery content and objectives.")
        self.fields['delivery_type'].help_text = _("Select whether this is a program or course delivery.")
        self.fields['program'].help_text = _("Select the program for this delivery (if delivery type is Program).")
        self.fields['course'].help_text = _("Select the course for this delivery (if delivery type is Course).")
        self.fields['delivery_mode'].help_text = _("Choose the mode of delivery (e.g., self-paced, instructor-led, blended).")
        self.fields['start_date'].help_text = _("Set the start date and time for this delivery.")
        self.fields['end_date'].help_text = _("Set the end date and time for this delivery.")
        self.fields['enrollment_start'].help_text = _("Set the date when enrollment for this delivery opens.")
        self.fields['enrollment_end'].help_text = _("Set the deadline for enrollment in this delivery.")
        self.fields['deactivation_date'].help_text = _("Optionally set a date when this delivery will be deactivated.")
        self.fields['max_participants'].help_text = _("Set the maximum number of participants allowed (leave blank for unlimited).")
        self.fields['is_active'].help_text = _("Indicate whether this delivery is currently active.")
        self.fields['is_mandatory'].help_text = _("Indicate whether this delivery is mandatory for enrolled participants.")
        self.fields['completion_criteria'].help_text = _("Select the criteria for marking this delivery as completed.")
        self.fields['minimum_score'].help_text = _("Set the minimum score required for completion (if applicable).")
        self.fields['attendance_threshold'].help_text = _("Set the minimum attendance percentage required (if applicable).")
        self.fields['issue_certificate'].help_text = _("Indicate whether a certificate should be issued upon completion.")
        self.fields['allow_self_unenroll'].help_text = _("Allow participants to unenroll themselves from this delivery.")

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        delivery_mode = cleaned_data.get('delivery_mode')
        program = cleaned_data.get('program')
        course = cleaned_data.get('course')
        instructors = cleaned_data.get('instructors')

        if delivery_type == 'PROGRAM' and not program:
            raise forms.ValidationError(_("Program delivery must have a program associated."))
        if delivery_type == 'COURSE' and not course:
            raise forms.ValidationError(_("Course delivery must have a course associated."))
        
        if delivery_mode == 'INSTRUCTOR_LED' and not instructors:
            raise forms.ValidationError(_("Instructor-led delivery must have at least one instructor."))

        completion_criteria = cleaned_data.get('completion_criteria')
        minimum_score = cleaned_data.get('minimum_score')
        attendance_threshold = cleaned_data.get('attendance_threshold')

        if completion_criteria == 'MINIMUM_SCORE' and minimum_score is None:
            raise forms.ValidationError(_("Minimum score must be set when using 'Achieve Minimum Score' completion criteria."))
        if completion_criteria == 'ATTENDANCE' and attendance_threshold is None:
            raise forms.ValidationError(_("Attendance threshold must be set when using 'Meet Attendance Requirement' completion criteria."))

        return cleaned_data

    def save(self, commit=True):
        delivery = super().save(commit=False)
        if commit:
            try:
                delivery.save()
                instructors = self.cleaned_data.get('instructors')
                if instructors:
                    for instructor in instructors:
                        DeliveryInstructor.objects.create(
                            delivery=delivery,
                            instructor=instructor,
                            role='PRIMARY',
                            assigned_by=self.user
                        )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving delivery: {str(e)}")
                raise
        return delivery
    
class DeliveryEditForm(forms.ModelForm):
    instructors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='facilitator'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Select one or more instructors for this delivery.")
    )

    class Meta:
        model = Delivery
        fields = [
            'title', 'description', 'delivery_type', 'delivery_mode', 
            'program', 'course', 'instructors',
            'start_date', 'end_date', 'enrollment_start',
            'enrollment_end', 'deactivation_date', 'max_participants',
            'is_active', 'is_mandatory', 'completion_criteria', 'minimum_score',
            'attendance_threshold', 'issue_certificate', 'allow_self_unenroll'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'enrollment_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'enrollment_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'deactivation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields['program'].queryset = Program.objects.filter(is_published=True)
        self.fields['course'].queryset = Course.objects.filter(is_published=True)

        # Disable changing of delivery type if the delivery has already started
        if self.instance.pk and self.instance.has_started():
            self.fields['delivery_type'].disabled = True
            self.fields['program'].disabled = True
            self.fields['course'].disabled = True

        # Add helper text to each field
        self.fields['title'].help_text = _("Enter a descriptive title for this delivery.")
        self.fields['description'].help_text = _("Provide a detailed description of the delivery content and objectives.")
        self.fields['delivery_type'].help_text = _("Select whether this is a program or course delivery.")
        self.fields['program'].help_text = _("Select the program for this delivery (if delivery type is Program).")
        self.fields['course'].help_text = _("Select the course for this delivery (if delivery type is Course).")
        self.fields['delivery_mode'].help_text = _("Choose the mode of delivery (e.g., self-paced, instructor-led, blended).")
        self.fields['start_date'].help_text = _("Set the start date and time for this delivery.")
        self.fields['end_date'].help_text = _("Set the end date and time for this delivery.")
        self.fields['enrollment_start'].help_text = _("Set the date when enrollment for this delivery opens.")
        self.fields['enrollment_end'].help_text = _("Set the deadline for enrollment in this delivery.")
        self.fields['deactivation_date'].help_text = _("Optionally set a date when this delivery will be deactivated.")
        self.fields['max_participants'].help_text = _("Set the maximum number of participants allowed (leave blank for unlimited).")
        self.fields['is_active'].help_text = _("Indicate whether this delivery is currently active.")
        self.fields['is_mandatory'].help_text = _("Indicate whether this delivery is mandatory for enrolled participants.")
        self.fields['completion_criteria'].help_text = _("Select the criteria for marking this delivery as completed.")
        self.fields['minimum_score'].help_text = _("Set the minimum score required for completion (if applicable).")
        self.fields['attendance_threshold'].help_text = _("Set the minimum attendance percentage required (if applicable).")
        self.fields['issue_certificate'].help_text = _("Indicate whether a certificate should be issued upon completion.")
        self.fields['allow_self_unenroll'].help_text = _("Allow participants to unenroll themselves from this delivery.")

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        delivery_mode = cleaned_data.get('delivery_mode')
        program = cleaned_data.get('program')
        course = cleaned_data.get('course')
        instructors = cleaned_data.get('instructors')

        if delivery_type == 'PROGRAM' and not program:
            raise forms.ValidationError(_("Program delivery must have a program associated."))
        if delivery_type == 'COURSE' and not course:
            raise forms.ValidationError(_("Course delivery must have a course associated."))
        
        if delivery_mode == 'INSTRUCTOR_LED' and not instructors:
            raise forms.ValidationError(_("Instructor-led delivery must have at least one instructor."))

        # Additional validation for editing
        if self.instance.pk and self.instance.has_started():
            if delivery_type != self.instance.delivery_type:
                raise forms.ValidationError(_("Cannot change delivery type for an ongoing delivery."))

        return cleaned_data

    def save(self, commit=True):
        delivery = super().save(commit=False)
        if commit:
            delivery.save()
            # Update instructors
            DeliveryInstructor.objects.filter(delivery=delivery).delete()
            for instructor in self.cleaned_data.get('instructors', []):
                DeliveryInstructor.objects.create(
                    delivery=delivery,
                    instructor=instructor,
                    role='PRIMARY',
                    assigned_by=self.user
                )
        return delivery

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

class CourseComponentForm(forms.ModelForm):
    class Meta:
        model = DeliveryComponent
        fields = ['program_course', 'is_mandatory', 'order']

    def __init__(self, *args, **kwargs):
        self.delivery = kwargs.pop('delivery', None)
        super().__init__(*args, **kwargs)
        if self.delivery:
            self.fields['program_course'].queryset = ProgramCourse.objects.filter(program=self.delivery.program)

class ResourceComponentForm(forms.ModelForm):
    class Meta:
        model = DeliveryComponent
        fields = ['learning_resource', 'is_mandatory', 'order']

    def __init__(self, *args, **kwargs):
        self.delivery = kwargs.pop('delivery', None)
        self.parent_component = kwargs.pop('parent_component', None)
        super().__init__(*args, **kwargs)
        
        if self.delivery:
            self.fields['learning_resource'].queryset = LearningResource.objects.filter(course=self.delivery.course)
        elif self.parent_component:
            self.fields['learning_resource'].queryset = LearningResource.objects.filter(course=self.parent_component.program_course.course)

# ============================================================
# ======================= Enrollment Forms ===================
# ============================================================

class EnrollmentForm(forms.ModelForm):
    selected_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Users"
    )

    class Meta:
        model = Enrollment
        fields = ['selected_users', 'status']

    def __init__(self, *args, **kwargs):
        delivery = kwargs.pop('delivery', None)
        user_queryset = kwargs.pop('user_queryset', User.objects.none())
        super(EnrollmentForm, self).__init__(*args, **kwargs)
        if delivery:
            self.instance.delivery = delivery
        self.fields['selected_users'].queryset = user_queryset
        self.fields['selected_users'].label_from_instance = self.label_from_instance
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

    @staticmethod
    def label_from_instance(user):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'gender': user.gender,
            'timezone': user.timezone,
            'organization': user.current_organization.name if user.current_organization else None,
            'organization_unit': user.current_organization_unit.name if user.current_organization_unit else None,
            'profile_picture': user.picture.url if user.picture else None,
        }
    
class EnrollmentEditForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['status', 'completion_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'completion_date': forms.DateTimeInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'type': 'datetime-local'}),
        }

class UserEnrollmentForm(forms.Form):
    enrollment_type = forms.ChoiceField(choices=[('program', 'Program'), ('course', 'Course')], widget=forms.HiddenInput())
    object_id = forms.UUIDField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        enrollment_type = cleaned_data.get('enrollment_type')
        object_id = cleaned_data.get('object_id')

        if enrollment_type == 'program':
            try:
                Program.objects.get(id=object_id)
            except Program.DoesNotExist:
                raise forms.ValidationError("Invalid program selected.")
        elif enrollment_type == 'course':
            try:
                Course.objects.get(id=object_id)
            except Course.DoesNotExist:
                raise forms.ValidationError("Invalid course selected.")

        return cleaned_data