from django.contrib import admin

from . import models

admin.site.register(models.Program)
admin.site.register(models.Course)
admin.site.register(models.ProgramCourse)
admin.site.register(models.LearningResource)
admin.site.register(models.Delivery)
admin.site.register(models.DeliveryComponent)
admin.site.register(models.Enrollment)
admin.site.register(models.ComponentCompletion)
admin.site.register(models.Tag)
admin.site.register(models.CourseCategory)
admin.site.register(models.Progress)
admin.site.register(models.ScormResource)
admin.site.register(models.ScormRegistration)
admin.site.register(models.Recommendation)
admin.site.register(models.Review)