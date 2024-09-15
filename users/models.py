"""Module docstring: This module defines models for the accounts app."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import pytz
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        default='male'
    )
    picture = models.ImageField(upload_to='user_pictures/', blank=True, null=True)
    timezone = models.CharField(
        max_length=50, 
        choices=[(tz, tz) for tz in pytz.common_timezones],
        default=timezone.get_current_timezone_name()
    )
    current_organization = models.ForeignKey('organization.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_users')
    current_organization_unit = models.ForeignKey('organization.OrganizationUnit', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_users')

    def get_current_role(self):
        current_assignment = self.organization_assignments.filter(
            organization=self.current_organization,
            organization_unit=self.current_organization_unit,
            is_active=True
        ).first()
        if current_assignment:
            return current_assignment.role
        return None

    def get_all_roles(self):
        return UserRole.objects.filter(user=self, is_active=True)

    def has_role(self, role_name):
        return self.get_all_roles().filter(role__name=role_name).exists()

class SCORMUserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scorm_profile')
    scorm_player_id = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=100, blank=True, null=True)

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE)
    organization_unit = models.ForeignKey('organization.OrganizationUnit', on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'role', 'organization', 'organization_unit', 'start_date']

    def __str__(self):
        return f"{self.user.username} - {self.role.name} in {self.organization.name}"

class UserOrganizationAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_assignments')
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE)
    organization_unit = models.ForeignKey('organization.OrganizationUnit', on_delete=models.CASCADE)
    job_position = models.ForeignKey('organization.JobPosition', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'organization', 'organization_unit', 'start_date']

    def __str__(self):
        return f"{self.user.username} in {self.organization.name} - {self.organization_unit.name}"

class VisibilityRule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    visibility_level = models.CharField(max_length=20, choices=[
        ('NONE', 'No Access'),
        ('READ', 'Read Only'),
        ('WRITE', 'Read and Write'),
        ('ADMIN', 'Full Admin Access'),
    ])

    class Meta:
        unique_together = ['role', 'content_type']

    def __str__(self):
        return f"{self.role.name} - {self.content_type.model} - {self.get_visibility_level_display()}"

def check_visibility(user, obj):
    user_role = user.get_current_role()
    if not user_role:
        return 'NONE'
    content_type = ContentType.objects.get_for_model(obj)
    try:
        rule = VisibilityRule.objects.get(role=user_role, content_type=content_type)
        return rule.visibility_level
    except VisibilityRule.DoesNotExist:
        return 'NONE'

class Learner(models.Model):
    """Model representing a learner."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

class Administrator(models.Model):
    """Model representing an administrator."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

class Supervisor(models.Model):
    """Model representing a supervisor."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

class Facilitator(models.Model):
    """Model representing a facilitator."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'