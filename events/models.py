# events/models.py

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

class Event(models.Model):
    EVENT_TYPES = (
        ('LECTURE', 'Lecture'),
        ('WEBINAR', 'Webinar'),
        ('WORKSHOP', 'Workshop'),
        ('EXAM', 'Exam'),
        ('ASSIGNMENT_DUE', 'Assignment Due'),
        ('COURSE_START', 'Course Start'),
        ('COURSE_END', 'Course End'),
        ('OFFICE_HOURS', 'Office Hours'),
        ('GROUP_MEETING', 'Group Meeting'),
        ('GUEST_SPEAKER', 'Guest Speaker'),
        ('ORIENTATION', 'Orientation'),
        ('DEADLINE', 'Deadline'),
        ('OTHER', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_virtual = models.BooleanField(default=False)
    virtual_meeting_link = models.URLField(blank=True, null=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='organized_events')
    is_public = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # For associating the event with a specific course, program, etc.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.title

class RecurringEvent(models.Model):
    RECURRENCE_TYPES = (
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-weekly'),
        ('MONTHLY', 'Monthly'),
    )

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='recurrence')
    recurrence_type = models.CharField(max_length=10, choices=RECURRENCE_TYPES)
    recurrence_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Recurring {self.event.title} - {self.get_recurrence_type_display()}"

class EventRegistration(models.Model):
    ATTENDANCE_STATUS = (
        ('REGISTERED', 'Registered'),
        ('ATTENDED', 'Attended'),
        ('ABSENT', 'Absent'),
        ('EXCUSED', 'Excused'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS, default='REGISTERED')
    attendance_marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    attendance_marked_at = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

class EventFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"Feedback for {self.event.title} by {self.user.username}"

class EventResource(models.Model):
    RESOURCE_TYPES = (
        ('PRESENTATION', 'Presentation'),
        ('DOCUMENT', 'Document'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('IMAGE', 'Image'),
        ('OTHER', 'Other'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='event_resources/')
    url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.event.title}"

class EventReminder(models.Model):
    REMINDER_TYPES = (
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPES)
    remind_before = models.DurationField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.event.title}"

class EventGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='event_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"