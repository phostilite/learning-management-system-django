import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.subject

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For associating the message with a specific course, lesson, etc.
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def _str_(self):
        return f"Message from {self.sender.username} in {self.thread.subject}"

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            self.thread.updated_at = timezone.now()
            self.thread.save()
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise

class Recipient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='recipients')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_threads')
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)

    class Meta:
        unique_together = ['thread', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.thread.subject}"

class Label(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#FFFFFF")  # Hex color code

    class Meta:
        unique_together = ['user', 'name']

    def _str_(self):
        return f"{self.user.username} - {self.name}"

class ThreadLabel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='threads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='thread_labels')

    class Meta:
        unique_together = ['thread', 'label', 'user']

    def _str_(self):
        return f"{self.user.username} - {self.thread.subject} - {self.label.name}"

class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # in bytes
    content_type = models.CharField(max_length=100)

    def _str_(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.file_size:
            self.file_size = self.file.size
        if not self.content_type:
            self.content_type = self.file.content_type
        super().save(*args, **kwargs)

class Draft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_drafts')
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='draft_recipients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"Draft by {self.user.username}: {self.subject}"

class UserMessageSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_settings')
    email_notifications = models.BooleanField(default=True)
    messages_per_page = models.PositiveIntegerField(default=50)
    signature = models.TextField(blank=True)

    def _str_(self):
        return f"Message settings for {self.user.username}"