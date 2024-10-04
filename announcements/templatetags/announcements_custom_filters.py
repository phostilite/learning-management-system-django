from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def is_author_in_group(announcement, group_name):
    try:
        group = Group.objects.get(name=group_name)
        return group in announcement.author.groups.all()
    except Group.DoesNotExist:
        return False