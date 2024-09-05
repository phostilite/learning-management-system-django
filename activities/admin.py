from django.contrib import admin

from . import models

admin.site.register(models.ActivityLog)
admin.site.register(models.SystemNotification)
admin.site.register(models.UserSession)

