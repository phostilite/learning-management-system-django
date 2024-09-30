# virtual_classroom/models.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from courses.models import Delivery
import uuid

class VirtualClassroomProvider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Provider Name"), max_length=100)
    api_key = models.CharField(_("API Key"), max_length=255)
    api_secret = models.CharField(_("API Secret"), max_length=255)
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Virtual Classroom Provider")
        verbose_name_plural = _("Virtual Classroom Providers")

    def __str__(self):
        return self.name

class VirtualClassroomSession(models.Model):
    PROVIDER_CHOICES = (
        ('TEAMS', _('Microsoft Teams')),
        ('ZOOM', _('Zoom')),
        ('MEET', _('Google Meet')),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='virtual_sessions')
    provider = models.ForeignKey(VirtualClassroomProvider, on_delete=models.PROTECT)
    provider_type = models.CharField(_("Provider Type"), max_length=10, choices=PROVIDER_CHOICES)
    meeting_id = models.CharField(_("Meeting ID"), max_length=255)
    meeting_password = models.CharField(_("Meeting Password"), max_length=255, blank=True, null=True)
    join_url = models.URLField(_("Join URL"))
    start_time = models.DateTimeField(_("Start Time"))
    end_time = models.DateTimeField(_("End Time"))
    is_recurring = models.BooleanField(_("Is Recurring"), default=False)
    recurrence_pattern = models.JSONField(_("Recurrence Pattern"), blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_virtual_sessions')
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Virtual Classroom Session")
        verbose_name_plural = _("Virtual Classroom Sessions")
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.get_provider_type_display()} Session for {self.delivery}"

class VirtualClassroomAttendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(VirtualClassroomSession, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='virtual_attendances')
    join_time = models.DateTimeField(_("Join Time"), null=True, blank=True)
    leave_time = models.DateTimeField(_("Leave Time"), null=True, blank=True)
    duration = models.DurationField(_("Duration"), null=True, blank=True)

    class Meta:
        verbose_name = _("Virtual Classroom Attendee")
        verbose_name_plural = _("Virtual Classroom Attendees")
        unique_together = ['session', 'user']

    def __str__(self):
        return f"{self.user} - {self.session}"