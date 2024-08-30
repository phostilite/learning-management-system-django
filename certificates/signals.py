# certificates/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import LearningProgress, LearningResource
from .models import Certificate
import logging
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

@receiver(post_save, sender=LearningProgress)
def check_course_completion(sender, instance, created, **kwargs):
    logger.info(f"Signal received for LearningProgress {instance.id}")
    if instance.is_completed:
        logger.info(f"LearningProgress {instance.id} is marked as completed")
        try:
            enrollment = instance.enrollment
            
            # Check if all learning resources are completed for this enrollment
            course = enrollment.course_delivery.course
            total_resources = LearningResource.objects.filter(course=course).count()
            completed_resources = LearningProgress.objects.filter(
                enrollment=enrollment,
                resource__course=course,
                is_completed=True
            ).count()
            
            logger.debug(f"Total resources: {total_resources}, Completed resources: {completed_resources}")
            
            if total_resources == completed_resources:
                logger.info(f"All resources completed for enrollment {enrollment.id}. Attempting to issue certificate.")
                try:
                    certificate = Certificate.issue_certificate(
                        enrollment,
                        issued_by=None,
                        ip_address=None,
                        user_agent=None
                    )
                    if certificate:
                        logger.info(f"Certificate {certificate.certificate_number} issued successfully")
                    else:
                        logger.warning(f"Certificate not issued for enrollment {enrollment.id}")
                except Exception as e:
                    logger.error(f"Error during certificate issuance: {str(e)}")
            else:
                logger.info(f"Not all resources completed for enrollment {enrollment.id}. Certificate not issued.")
        except ObjectDoesNotExist:
            logger.error(f"Related object not found for LearningProgress {instance.id}")
        except Exception as e:
            logger.error(f"Unexpected error in check_course_completion: {str(e)}")