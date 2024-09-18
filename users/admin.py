from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SCORMUserProfile, Role, UserRole, UserOrganizationAssignment, VisibilityRule

class SCORMUserProfileInline(admin.StackedInline):
    model = SCORMUserProfile
    can_delete = False
    verbose_name_plural = 'SCORM User Profile'

class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1

class UserOrganizationAssignmentInline(admin.TabularInline):
    model = UserOrganizationAssignment
    extra = 1

class UserAdmin(BaseUserAdmin):
    inlines = (SCORMUserProfileInline, UserRoleInline, UserOrganizationAssignmentInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'current_organization', 'current_organization_unit')
    list_filter = BaseUserAdmin.list_filter + ('current_organization', 'current_organization_unit')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'picture', 'timezone')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Organization'), {'fields': ('current_organization', 'current_organization_unit')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'picture', 'timezone')}),
        (_('Organization'), {'fields': ('current_organization', 'current_organization_unit')}),
    )

admin.site.register(User, UserAdmin)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization', 'organization_unit', 'start_date', 'end_date', 'is_active')
    list_filter = ('role', 'organization', 'organization_unit', 'is_active')
    search_fields = ('user__username', 'role__name', 'organization__name', 'organization_unit__name')

@admin.register(UserOrganizationAssignment)
class UserOrganizationAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'organization_unit', 'job_position', 'start_date', 'end_date', 'is_active')
    list_filter = ('organization', 'organization_unit', 'job_position', 'is_active')
    search_fields = ('user__username', 'organization__name', 'organization_unit__name', 'job_position__title')

@admin.register(VisibilityRule)
class VisibilityRuleAdmin(admin.ModelAdmin):
    list_display = ('role', 'content_type', 'visibility_level')
    list_filter = ('role', 'content_type', 'visibility_level')
    search_fields = ('role__name', 'content_type__model')