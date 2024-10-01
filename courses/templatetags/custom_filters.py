from django import template
from uuid import UUID
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
@stringfilter
def split(value, arg):
    return value.split(arg)

@register.filter
@stringfilter
def file_extension(value):
    return value.split('.')[-1].lower()

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})