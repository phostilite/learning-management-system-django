import django_filters
from django import forms
from .models import Announcement

class AnnouncementFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    priority = django_filters.ChoiceFilter(choices=Announcement.PRIORITY_CHOICES)
    publish_date_after = django_filters.DateFilter(field_name='publish_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    publish_date_before = django_filters.DateFilter(field_name='publish_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = Announcement
        fields = ['title', 'priority', 'publish_date_after', 'publish_date_before']