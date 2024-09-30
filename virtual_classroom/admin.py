# virtual_classroom/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import VirtualClassroomProvider, VirtualClassroomSession, VirtualClassroomAttendee

@admin.register(VirtualClassroomProvider)
class VirtualClassroomProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'api_key_masked')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('id',)
    fieldsets = (
        (None, {'fields': ('id', 'name', 'is_active')}),
        (_('API Information'), {'fields': ('api_key', 'api_secret'), 'classes': ('collapse',)}),
    )

    def api_key_masked(self, obj):
        return f"{obj.api_key[:5]}{'*' * (len(obj.api_key) - 5)}"
    api_key_masked.short_description = _("API Key")

@admin.register(VirtualClassroomSession)
class VirtualClassroomSessionAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'provider_type', 'start_time', 'end_time', 'is_recurring', 'attendee_count', 'join_link')
    list_filter = ('provider_type', 'is_recurring', 'start_time', 'provider')
    search_fields = ('delivery__title', 'meeting_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'attendee_count')
    raw_id_fields = ('delivery', 'created_by')
    date_hierarchy = 'start_time'
    fieldsets = (
        (None, {'fields': ('id', 'delivery', 'provider', 'provider_type')}),
        (_('Meeting Details'), {'fields': ('meeting_id', 'meeting_password', 'join_url')}),
        (_('Schedule'), {'fields': ('start_time', 'end_time', 'is_recurring', 'recurrence_pattern')}),
        (_('Meta'), {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def attendee_count(self, obj):
        return obj.attendees.count()
    attendee_count.short_description = _("Attendees")

    def join_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.join_url, _("Join"))
    join_link.short_description = _("Join URL")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('delivery', 'provider').prefetch_related('attendees')

@admin.register(VirtualClassroomAttendee)
class VirtualClassroomAttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_info', 'join_time', 'leave_time', 'duration')
    list_filter = ('session__provider_type', 'join_time')
    search_fields = ('user__username', 'user__email', 'session__meeting_id')
    readonly_fields = ('id', 'duration')
    raw_id_fields = ('user', 'session')
    date_hierarchy = 'join_time'
    
    def session_info(self, obj):
        return f"{obj.session.provider_type} - {obj.session.start_time.strftime('%Y-%m-%d %H:%M')}"
    session_info.short_description = _("Session")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'session')