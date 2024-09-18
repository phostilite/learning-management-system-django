from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
import pytz
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
import uuid
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        try:
            current_assignment = self.organization_assignments.get(
                organization=self.current_organization,
                organization_unit=self.current_organization_unit,
                is_active=True
            )
            return current_assignment.role
        except UserOrganizationAssignment.DoesNotExist:
            logger.warning(f"No active role found for user {self.username} in current organization and unit.")
            return None
        except UserOrganizationAssignment.MultipleObjectsReturned:
            logger.error(f"Multiple active roles found for user {self.username} in current organization and unit.")
            return None

    def get_all_roles(self):
        return UserRole.objects.filter(user=self, is_active=True)

    def has_role(self, role_name):
        return self.get_all_roles().filter(role__name=role_name).exists()

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving user {self.username}: {str(e)}")
            raise

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    access_level = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving role {self.name}: {str(e)}")
            raise

class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
            super().save(*args, **kwargs)
        except ValidationError as e:
            logger.error(f"Validation error saving UserRole: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error saving UserRole: {str(e)}")
            raise

class UserOrganizationAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
            super().save(*args, **kwargs)
        except ValidationError as e:
            logger.error(f"Validation error saving UserOrganizationAssignment: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error saving UserOrganizationAssignment: {str(e)}")
            raise

class VisibilityRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving VisibilityRule: {str(e)}")
            raise

def check_visibility(user, obj):
    try:
        user_role = user.get_current_role()
        if not user_role:
            return 'NONE'
        content_type = ContentType.objects.get_for_model(obj)
        rule = VisibilityRule.objects.get(role=user_role, content_type=content_type)
        return rule.visibility_level
    except VisibilityRule.DoesNotExist:
        logger.warning(f"No VisibilityRule found for user {user.username} and object {obj}")
        return 'NONE'
    except Exception as e:
        logger.error(f"Error checking visibility for user {user.username} and object {obj}: {str(e)}")
        return 'NONE'

class SCORMUserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scorm_profile')
    scorm_player_id = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"SCORM Profile for {self.user.username}"

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving SCORMUserProfile for user {self.user.username}: {str(e)}")
            raise