from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
import pytz
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
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
    bio = models.TextField(blank=True, null=True)

    # New fields
    preferred_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French')],  # Add more languages as needed
        default='en'
    )
    email_notifications_enabled = models.BooleanField(default=True)
    sms_notifications_enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving user {self.username}: {str(e)}")
            raise

    def has_advanced_permission(self, base_permission):
        if self.is_superuser:
            return True
        
        try:
            job_position = self.employee_profile.job_position
            if not job_position:
                return False

            job_level = job_position.level
            
            for level in range(job_level, 0, -1):
                if self.has_perm(f'{base_permission}_level{level}'):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking advanced permission for user {self.username}: {str(e)}")
            return False

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

def create_default_groups_and_permissions():
    try:
        # Create default groups
        learner_group, _ = Group.objects.get_or_create(name='Learner')
        facilitator_group, _ = Group.objects.get_or_create(name='Facilitator')
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        administrator_group, _ = Group.objects.get_or_create(name='Administrator')

        # Create permissions (example - adjust as needed)
        content_type = ContentType.objects.get_for_model(User)
        view_course_perm, _ = Permission.objects.get_or_create(
            codename='view_course',
            name='Can view course',
            content_type=content_type
        )
        edit_course_perm, _ = Permission.objects.get_or_create(
            codename='edit_course',
            name='Can edit course',
            content_type=content_type
        )

        # Assign permissions to groups
        learner_group.permissions.add(view_course_perm)
        facilitator_group.permissions.add(view_course_perm, edit_course_perm)
        supervisor_group.permissions.add(view_course_perm, edit_course_perm)
        administrator_group.permissions.set(Permission.objects.all())

    except Exception as e:
        logger.error(f"Error creating default groups and permissions: {str(e)}")
        raise