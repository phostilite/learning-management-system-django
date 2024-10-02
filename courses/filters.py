from django import forms
import django_filters
from django_filters import DateTimeFilter
from django.forms import DateTimeInput
from .models import Course, Program, CourseCategory, Delivery, Enrollment
from users.models import User

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


class ProgramFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Title')
    program_type = django_filters.ChoiceFilter(choices=Program.PROGRAM_TYPES)
    level = django_filters.CharFilter(lookup_expr='icontains', label='Level')
    provider = django_filters.CharFilter(lookup_expr='icontains', label='Provider')
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
        model = Program
        fields = ['title', 'program_type', 'level', 'provider', 'is_published', 'created_at_after', 'created_at_before', 'created_by']

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