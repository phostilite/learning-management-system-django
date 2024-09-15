from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
import uuid

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Organization(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    founded_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True)

    def __str__(self):
        return self.name
    
    def get_all_users(self):
        return settings.AUTH_USER_MODEL.objects.filter(
            userrole__organization=self,
            userrole__is_active=True
        ).distinct()

class OrganizationUnit(TimeStampedModel):
    UNIT_TYPES = (
        ('COMPANY', 'Company'),
        ('DIVISION', 'Division'),
        ('DEPARTMENT', 'Department'),
        ('TEAM', 'Team'),
        ('SUB_TEAM', 'Sub Team'),
        ('PROJECT', 'Project'),
        ('OTHER', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=255)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES, default='OTHER')
    code = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_units')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    level = models.PositiveIntegerField(default=0, editable=False)

    def __str__(self):
        return f"{self.organization.name} - {self.name} ({self.get_unit_type_display()})"

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)

    def clean(self):
        if self.parent and self.parent.organization != self.organization:
            raise ValidationError(_("Parent unit must belong to the same organization."))

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]

    def get_descendants(self):
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def is_descendant_of(self, other_unit):
        current = self.parent
        while current:
            if current == other_unit:
                return True
            current = current.parent
        return False

    @property
    def depth(self):
        return len(self.get_ancestors())

    class Meta:
        ordering = ['organization', 'level', 'name']
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'level']),
        ]

    def get_users(self):
        return settings.AUTH_USER_MODEL.objects.filter(
            userrole__organization=self.organization,
            userrole__organization_unit=self,
            userrole__is_active=True
        ).distinct()

    def get_managers(self):
        return settings.AUTH_USER_MODEL.objects.filter(
            userrole__organization=self.organization,
            userrole__organization_unit=self,
            userrole__role__name='Manager',  
            userrole__is_active=True
        ).distinct()

class Location(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_headquarters = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

class JobPosition(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='job_positions')
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_manager_position = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subordinate_positions')

    def __str__(self):
        return f"{self.organization.name} - {self.title}"
    
    def get_users(self):
        return settings.AUTH_USER_MODEL.objects.filter(
            userorganizationassignment__organization=self.organization,
            userorganizationassignment__job_position=self,
            userorganizationassignment__is_active=True
        ).distinct()

class EmployeeProfile(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='employees')
    employee_id = models.CharField(max_length=50, unique=True)
    job_position = models.ForeignKey(JobPosition, on_delete=models.SET_NULL, null=True, related_name='employees')
    organization_unit = models.ForeignKey(OrganizationUnit, on_delete=models.SET_NULL, null=True, related_name='employees')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='subordinates')
    current_assignment = models.ForeignKey('users.UserOrganizationAssignment', on_delete=models.SET_NULL, null=True, related_name='current_profile')
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='employees')
    work_phone = models.CharField(max_length=20, blank=True)
    work_email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"
    
    def get_current_role(self):
        return self.user.get_current_role()

    def get_all_roles(self):
        return self.user.get_all_roles()

class OrganizationContact(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

class CustomField(TimeStampedModel):
    FIELD_TYPES = (
        ('TEXT', 'Text'),
        ('NUMBER', 'Number'),
        ('DATE', 'Date'),
        ('BOOLEAN', 'Boolean'),
        ('CHOICE', 'Choice'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='custom_fields')
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    choices = models.JSONField(null=True, blank=True)  # For CHOICE type fields

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

class CustomFieldValue(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    custom_field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='values')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    value = models.JSONField()

    def __str__(self):
        return f"{self.custom_field.name} - {self.content_object}"

class OrganizationChange(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='changes')
    change_type = models.CharField(max_length=50)  # e.g., 'RESTRUCTURE', 'MERGER', 'ACQUISITION'
    description = models.TextField()
    effective_date = models.DateField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_org_changes')

    def __str__(self):
        return f"{self.organization.name} - {self.change_type} - {self.effective_date}"

class TeamMembership(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='team_memberships')
    team = models.ForeignKey(OrganizationUnit, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.team.name}"

    def clean(self):
        if self.team.unit_type != 'TEAM':
            raise ValidationError(_("The selected organization unit must be a team."))