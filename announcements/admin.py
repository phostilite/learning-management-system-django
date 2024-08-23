from django.contrib import admin

from .models import Announcement, AnnouncementRead, AnnouncementRecipient

admin.site.register(Announcement)
admin.site.register(AnnouncementRead)
admin.site.register(AnnouncementRecipient)
