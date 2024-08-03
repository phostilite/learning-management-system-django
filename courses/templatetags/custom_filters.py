from django import template
from uuid import UUID

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(key, str):
        try:
            key = UUID(key)
        except ValueError:
            pass
    return dictionary.get(key)