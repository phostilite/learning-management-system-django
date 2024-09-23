import django_filters
from courses.models import Program, Course, Tag, CourseCategory
from organization.models import EmployeeProfile, OrganizationUnit, JobPosition
from activities.models import SystemNotification
from .mixins import AdministratorRequiredMixin
from django.db import models
from django import forms

class ProgramFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    program_type = django_filters.ChoiceFilter(choices=Program.PROGRAM_TYPES)
    level = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Program
        fields = ['title', 'program_type', 'level', 'tags']

class CourseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=CourseCategory.objects.all())
    difficulty_level = django_filters.ChoiceFilter(choices=Course.DIFFICULTY_LEVELS)
    language = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Course
        fields = ['title', 'category', 'difficulty_level', 'language', 'tags']

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

class EmployeeProfileFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')
    organization_unit = django_filters.ModelChoiceFilter(queryset=OrganizationUnit.objects.all())
    job_position = django_filters.ModelChoiceFilter(queryset=JobPosition.objects.all())
    is_active = django_filters.BooleanFilter()
    hire_date = django_filters.DateFromToRangeFilter()

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