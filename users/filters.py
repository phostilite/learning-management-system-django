import django_filters
from courses.models import Program, Course, Tag, CourseCategory, Delivery, Enrollment
from organization.models import EmployeeProfile, OrganizationUnit, JobPosition, Organization, Location
from django_filters import FilterSet, CharFilter, ModelChoiceFilter, BooleanFilter, DateFromToRangeFilter, DateFilter, NumberFilter, ChoiceFilter
from activities.models import SystemNotification
from .mixins import AdministratorRequiredMixin
from django.contrib.auth.models import Group
from django.db import models
from django import forms
import logging
from django.db.models import Q
from django.contrib.auth import get_user_model
import pytz
from django_filters import DateTimeFilter
from django.forms import DateTimeInput

User = get_user_model()

logger = logging.getLogger(__name__)

class UserFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    gender = django_filters.ChoiceFilter(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    timezone = django_filters.ChoiceFilter(choices=[(tz, tz) for tz in pytz.common_timezones])
    current_organization = django_filters.ModelChoiceFilter(queryset=Organization.objects.all())
    current_organization_unit = django_filters.ModelChoiceFilter(queryset=OrganizationUnit.objects.all())

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'timezone', 'current_organization', 'current_organization_unit']


class ProgramFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    program_type = django_filters.ChoiceFilter(choices=Program.PROGRAM_TYPES)
    level = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Program
        fields = ['title', 'program_type', 'level', 'tags']

class CourseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Title')
    category = django_filters.ModelChoiceFilter(queryset=CourseCategory.objects.all())
    difficulty_level = django_filters.ChoiceFilter(choices=Course.DIFFICULTY_LEVELS)
    is_published = django_filters.BooleanFilter()
    created_at_after = DateTimeFilter(
        field_name='created_at', 
        lookup_expr='gte', 
        label='Created after',
        widget=DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    created_at_before = DateTimeFilter(
        field_name='created_at', 
        lookup_expr='lte', 
        label='Created before',
        widget=DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    created_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Course
        fields = ['title', 'category', 'difficulty_level', 'is_published', 'created_at_after', 'created_at_before', 'created_by']

class DeliveryFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Title')
    delivery_type = django_filters.ChoiceFilter(choices=Delivery.DELIVERY_TYPES)
    delivery_mode = django_filters.ChoiceFilter(choices=Delivery.DELIVERY_MODES)
    start_date = django_filters.DateFilter(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = django_filters.DateFilter(widget=forms.DateInput(attrs={'type': 'date'}))
    is_active = django_filters.BooleanFilter(
        widget=forms.Select(choices=((None, 'All'), (True, 'Active'), (False, 'Inactive')))
    )
    completion_criteria = django_filters.ChoiceFilter(choices=Delivery.COMPLETION_CRITERIA)
    is_mandatory = django_filters.BooleanFilter()

    class Meta:
        model = Delivery
        fields = [
            'title', 'delivery_type', 'delivery_mode', 'start_date', 'end_date',
            'is_active', 'completion_criteria', 'is_mandatory'
        ]

class EnrollmentFilter(django_filters.FilterSet):
    user__username = django_filters.CharFilter(lookup_expr='icontains', label='Username')
    user__email = django_filters.CharFilter(lookup_expr='icontains', label='Email')
    status = django_filters.ChoiceFilter(choices=[
        ('ENROLLED', 'Enrolled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
    ])
    enrollment_date_after = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    enrollment_date_before = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))
    completion_date_after = django_filters.DateFilter(field_name='completion_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    completion_date_before = django_filters.DateFilter(field_name='completion_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Enrollment
        fields = ['user__username', 'user__email', 'status', 'enrollment_date_after', 'enrollment_date_before', 'completion_date_after', 'completion_date_before']


class NotificationFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='timestamp',
        lookup_expr='gte',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = django_filters.DateFilter(
        field_name='timestamp',
        lookup_expr='lte',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = SystemNotification
        fields = ['start_date', 'end_date']

class EmployeeProfileFilter(FilterSet):
    search = CharFilter(method='filter_search', label='Search')
    organization_unit = ModelChoiceFilter(queryset=OrganizationUnit.objects.all())
    job_position = ModelChoiceFilter(queryset=JobPosition.objects.all())
    is_active = BooleanFilter()
    hire_date = DateFilter()  

    class Meta:
        model = EmployeeProfile
        fields = ['search', 'organization_unit', 'job_position', 'is_active', 'hire_date']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(user__first_name__icontains=value) |
            models.Q(user__last_name__icontains=value) |
            models.Q(user__email__icontains=value) |
            models.Q(employee_id__icontains=value)
        )
    
class JobPositionFilter(FilterSet):
    search = CharFilter(method='filter_search', label='Search')
    organization = ModelChoiceFilter(queryset=Organization.objects.all())
    level = NumberFilter()
    is_manager_position = BooleanFilter()

    class Meta:
        model = JobPosition
        fields = ['search', 'organization', 'level', 'is_manager_position']

    def filter_search(self, queryset, name, value):
        try:
            return queryset.filter(
                models.Q(title__icontains=value) |
                models.Q(code__icontains=value) |
                models.Q(description__icontains=value)
            )
        except Exception as e:
            logger.error(f"Error in JobPositionFilter filter_search: {str(e)}")
            return queryset.none()
        
class LocationFilter(FilterSet):
    search = CharFilter(method='filter_search', label='Search')
    organization = ModelChoiceFilter(queryset=Organization.objects.all())
    country = CharFilter(lookup_expr='icontains')
    is_headquarters = BooleanFilter()

    class Meta:
        model = Location
        fields = ['search', 'organization', 'country', 'is_headquarters']

    def filter_search(self, queryset, name, value):
        try:
            return queryset.filter(
                models.Q(name__icontains=value) |
                models.Q(city__icontains=value) |
                models.Q(state__icontains=value) |
                models.Q(postal_code__icontains=value)
            )
        except Exception as e:
            logger.error(f"Error in LocationFilter filter_search: {str(e)}")
            return queryset.none()
        
class GroupFilter(FilterSet):
    search = CharFilter(method='filter_search', label='Search')

    class Meta:
        model = Group
        fields = ['search']

    def filter_search(self, queryset, name, value):
        try:
            return queryset.filter(name__icontains=value)
        except Exception as e:
            logger.error(f"Error in GroupFilter filter_search: {str(e)}")
            return queryset.none()
        
class OrganizationUnitFilter(FilterSet):
    search = CharFilter(method='filter_search', label='Search')
    organization = ModelChoiceFilter(queryset=Organization.objects.all())
    unit_type = ChoiceFilter(choices=OrganizationUnit.UNIT_TYPES)
    is_active = BooleanFilter()

    class Meta:
        model = OrganizationUnit
        fields = ['search', 'organization', 'unit_type', 'is_active']

    def filter_search(self, queryset, name, value):
        try:
            return queryset.filter(
                models.Q(name__icontains=value) |
                models.Q(code__icontains=value) |
                models.Q(description__icontains=value)
            )
        except Exception as e:
            logger.error(f"Error in OrganizationUnitFilter filter_search: {str(e)}")
            return queryset.none()