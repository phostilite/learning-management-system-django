from django import template
from uuid import UUID
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(key, str):
        try:
            key = UUID(key)
        except ValueError:
            pass
    return dictionary.get(key)

@register.filter
@stringfilter
def split(value, arg):
    return value.split(arg)

@register.filter
@stringfilter
def file_extension(value):
    return value.split('.')[-1].lower()