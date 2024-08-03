"""Module docstring: This module defines models for the accounts app."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import pytz

class User(AbstractUser):
    """User model with extended fields."""
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

class Learner(models.Model):
    """Model representing a learner."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

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