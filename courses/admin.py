from django.contrib import admin

from . import models

admin.site.register(models.Course)
admin.site.register(models.CourseCategory)
admin.site.register(models.LearningResource)
admin.site.register(models.ScormResource)
admin.site.register(models.ScormRegistration)
admin.site.register(models.Enrollment)

admin.site.register(models.Program)
admin.site.register(models.Tag)