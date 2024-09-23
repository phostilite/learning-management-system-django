import django_filters
from django import forms
from django.db import models
from courses.models import Program, Course, Tag, CourseCategory
from announcements.models import Announcement
from django.utils.translation import gettext_lazy as _


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

class AnnouncementFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    priority = django_filters.ChoiceFilter(choices=Announcement.PRIORITY_CHOICES)
    publish_date_after = django_filters.DateFilter(field_name='publish_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    publish_date_before = django_filters.DateFilter(field_name='publish_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = Announcement
        fields = ['title', 'priority', 'publish_date_after', 'publish_date_before']