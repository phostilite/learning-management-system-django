from django.contrib import admin

from . import models

admin.site.register(models.Event)
admin.site.register(models.EventFeedback)
admin.site.register(models.RecurringEvent)
admin.site.register(models.EventRegistration)
admin.site.register(models.EventResource)
admin.site.register(models.EventGroup)