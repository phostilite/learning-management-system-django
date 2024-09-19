from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.auth import get_user_model
from .models import (
    Organization,
    OrganizationUnit,
    Location,
    JobPosition,
    EmployeeProfile,
    OrganizationContact,
    CustomField,
    CustomFieldValue,
    OrganizationChange,
    TeamMembership
)

User = get_user_model()

class OrganizationUnitInline(admin.TabularInline):
    model = OrganizationUnit
    extra = 1
    show_change_link = True

class LocationInline(admin.TabularInline):
    model = Location
    extra = 1

class JobPositionInline(admin.TabularInline):
    model = JobPosition
    extra = 1

class OrganizationContactInline(admin.TabularInline):
    model = OrganizationContact
    extra = 1

class CustomFieldInline(admin.TabularInline):
    model = CustomField
    extra = 1

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'legal_name', 'founded_date', 'industry')
    search_fields = ('name', 'legal_name', 'industry')
    list_filter = ('industry',)
    inlines = [OrganizationUnitInline, LocationInline, JobPositionInline, OrganizationContactInline, CustomFieldInline]
    fieldsets = (
        (None, {'fields': ('name', 'legal_name', 'description')}),
        ('Details', {'fields': ('tax_id', 'registration_number', 'founded_date', 'industry')}),
        ('Online Presence', {'fields': ('website', 'logo')}),
    )

@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'unit_type', 'parent', 'manager', 'is_active')
    list_filter = ('organization', 'unit_type', 'is_active')
    search_fields = ('name', 'code', 'manager__username')
    raw_id_fields = ('parent', 'manager')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'city', 'country', 'is_headquarters')
    list_filter = ('organization', 'country', 'is_headquarters')
    search_fields = ('name', 'city', 'country')

@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'code', 'level', 'is_manager_position')
    list_filter = ('organization', 'is_manager_position', 'level')
    search_fields = ('title', 'code')

class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'organization', 'job_position', 'hire_date', 'is_active')
    list_filter = ('organization', 'is_active', 'hire_date', 'job_position__level')
    search_fields = ('user__username', 'user__email', 'employee_id')
    raw_id_fields = ('user', 'job_position', 'organization_unit', 'manager')
    inlines = [TeamMembershipInline]
    fieldsets = (
        (None, {'fields': ('user', 'organization', 'employee_id')}),
        ('Job Information', {'fields': ('job_position', 'organization_unit', 'manager')}),
        ('Dates', {'fields': ('hire_date', 'termination_date')}),
        ('Status', {'fields': ('is_active',)}),
        ('Contact', {'fields': ('work_phone', 'work_email')}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(groups__name__in=['Learner', 'Facilitator', 'Supervisor', 'Administrator'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(OrganizationContact)
class OrganizationContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'email', 'position', 'is_primary')
    list_filter = ('organization', 'is_primary')
    search_fields = ('name', 'email', 'position')

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'field_type', 'is_required')
    list_filter = ('organization', 'field_type', 'is_required')
    search_fields = ('name',)

class CustomFieldValueInline(GenericTabularInline):
    model = CustomFieldValue
    extra = 1

@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    list_display = ('custom_field', 'content_type', 'object_id', 'value')
    list_filter = ('custom_field', 'content_type')
    search_fields = ('custom_field__name', 'value')

@admin.register(OrganizationChange)
class OrganizationChangeAdmin(admin.ModelAdmin):
    list_display = ('organization', 'change_type', 'effective_date', 'approved_by')
    list_filter = ('organization', 'change_type', 'effective_date')
    search_fields = ('organization__name', 'description')
    raw_id_fields = ('approved_by',)

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'team', 'role', 'start_date', 'end_date', 'is_active')
    list_filter = ('team', 'is_active')
    search_fields = ('employee__user__username', 'team__name', 'role')
    raw_id_fields = ('employee', 'team')