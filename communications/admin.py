from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Thread, Message, Recipient, Label, ThreadLabel, Attachment, Draft, UserMessageSettings
import logging

logger = logging.getLogger(__name__)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'content', 'created_at')
    readonly_fields = ('created_at',)

class RecipientInline(admin.TabularInline):
    model = Recipient
    extra = 0
    fields = ('user', 'is_read', 'is_archived', 'is_starred')

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('subject',)
    inlines = [MessageInline, RecipientInline]
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving Thread in admin: {str(e)}")
            raise ValidationError(_("An error occurred while saving the thread. Please try again."))

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'thread', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'sender')
    search_fields = ('content', 'sender_username', 'thread_subject')
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving Message in admin: {str(e)}")
            raise ValidationError(_("An error occurred while saving the message. Please try again."))

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('user', 'thread', 'is_read', 'is_archived', 'is_starred')
    list_filter = ('is_read', 'is_archived', 'is_starred')
    search_fields = ('user_username', 'thread_subject')

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')
    list_filter = ('user',)
    search_fields = ('name', 'user__username')

@admin.register(ThreadLabel)
class ThreadLabelAdmin(admin.ModelAdmin):
    list_display = ('thread', 'label', 'user')
    list_filter = ('label', 'user')
    search_fields = ('thread_subject', 'labelname', 'user_username')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'message', 'file_size', 'content_type')
    list_filter = ('content_type',)
    search_fields = ('filename', 'message__content')

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving Attachment in admin: {str(e)}")
            raise ValidationError(_("An error occurred while saving the attachment. Please try again."))

@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('subject', 'content', 'user__username')
    filter_horizontal = ('recipients',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserMessageSettings)
class UserMessageSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'messages_per_page')
    list_filter = ('email_notifications',)
    search_fields = ('user__username',)

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving UserMessageSettings in admin: {str(e)}")
            raise ValidationError(_("An error occurred while saving the user message settings. Please try again."))