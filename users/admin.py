from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SCORMUserProfile
from organization.models import EmployeeProfile

class SCORMUserProfileInline(admin.StackedInline):
    model = SCORMUserProfile
    can_delete = False
    verbose_name_plural = 'SCORM User Profile'

class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name_plural = 'Employee Profile'
    fk_name = 'user'  # Specify the ForeignKey to use

class UserAdmin(BaseUserAdmin):
    inlines = (SCORMUserProfileInline, EmployeeProfileInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'current_organization', 'current_organization_unit')
    list_filter = BaseUserAdmin.list_filter + ('current_organization', 'current_organization_unit', 'groups')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'picture', 'timezone', 'bio')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Organization'), {'fields': ('current_organization', 'current_organization_unit')}),
        (_('Preferences'), {'fields': ('preferred_language', 'email_notifications_enabled', 'sms_notifications_enabled')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'picture', 'timezone', 'bio')}),
        (_('Organization'), {'fields': ('current_organization', 'current_organization_unit')}),
        (_('Preferences'), {'fields': ('preferred_language', 'email_notifications_enabled', 'sms_notifications_enabled')}),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)

admin.site.register(User, UserAdmin)

@admin.register(SCORMUserProfile)
class SCORMUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'scorm_player_id')
    search_fields = ('user__username', 'scorm_player_id')