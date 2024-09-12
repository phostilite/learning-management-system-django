# certificates/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import Progress, LearningResource
from .models import Certificate
import logging
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Progress)
def check_course_completion(sender, instance, created, **kwargs):
    logger.info(f"Signal received for LearningProgress {instance.id}")
    