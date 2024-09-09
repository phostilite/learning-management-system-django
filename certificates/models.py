# certificates/models.py

import logging
from django.db import models
import uuid
from django.conf import settings
from courses.models import Course, Enrollment, LearningResource, Delivery, Progress
from users.models import User, Learner
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
import io
import os
from django.core.files.base import ContentFile
from django.db.models import Count
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='certificates', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates', null=True, blank=True)
    course_delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='certificates', null=True, blank=True)
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate', null=True, blank=True)

    certificate_number = models.CharField(max_length=50, unique=True)
    certificate_image = models.ImageField(upload_to='certificates/', null=True, blank=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    grade = models.CharField(max_length=10, blank=True, null=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    certificate_template = models.ForeignKey('CertificateTemplate', on_delete=models.SET_NULL, null=True, blank=True)

    is_valid = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_certificates')
    revocation_reason = models.TextField(blank=True)

    additional_info = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('learner', 'course', 'course_delivery')
        indexes = [
            models.Index(fields=['certificate_number']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['learner', 'course']),
        ]

    def __str__(self):
        return f"Certificate {self.certificate_number} for {self.learner.user.get_full_name()} - {self.course.title}"

    @classmethod
    def generate_certificate_number(cls):
        return f"CERT-{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    def issue_certificate(cls, enrollment, issued_by=None, ip_address=None, user_agent=None):
        logger.info(f"Attempting to issue certificate for enrollment {enrollment.id}")
        
        try:
            with transaction.atomic():
                # Verify the enrollment is valid and related to a course delivery
                if not enrollment.course_delivery:
                    logger.error(f"Enrollment {enrollment.id} is not associated with a course delivery")
                    return None

                # Get all learning resources for the course
                learning_resources = LearningResource.objects.filter(course=enrollment.course_delivery.course)
                total_resources = learning_resources.count()
                logger.debug(f"Total learning resources for course: {total_resources}")

                if total_resources == 0:
                    logger.warning(f"No learning resources found for course {enrollment.course_delivery.course.id}")
                    return None

                # Get completed learning progress for this enrollment
                completed_progress = Progress.objects.filter(
                    enrollment=enrollment,
                    resource__in=learning_resources,
                    is_completed=True
                ).count()
                logger.debug(f"Completed learning progress for enrollment: {completed_progress}")

                if completed_progress == total_resources:
                    logger.info("All learning resources completed. Proceeding with certificate issuance.")
                    
                    # Check if a certificate already exists
                    existing_certificate = cls.objects.filter(enrollment=enrollment).first()
                    if existing_certificate:
                        logger.warning(f"Certificate already exists for enrollment {enrollment.id}. Skipping issuance.")
                        return existing_certificate

                    # Generate and issue the certificate
                    certificate_number = cls.generate_certificate_number()
                    user_name = f"{enrollment.user.first_name} {enrollment.user.last_name}"
                    course_name = enrollment.course_delivery.course.title

                    # Get the default certificate template
                    template = CertificateTemplate.objects.filter(is_default=True).first()
                    if not template:
                        template = CertificateTemplate.objects.first()
                        if not template:
                            logger.error("No certificate template available")
                            raise ValueError("No certificate template available")

                    try:
                        certificate_image = cls.generate_certificate_image(user_name, course_name, certificate_number, template)
                    except Exception as e:
                        logger.error(f"Error generating certificate image: {str(e)}")
                        raise

                    try:
                        certificate = cls.objects.create(
                            learner=enrollment.user.learner,
                            course=enrollment.course_delivery.course,
                            course_delivery=enrollment.course_delivery,
                            enrollment=enrollment,
                            certificate_number=certificate_number,
                            certificate_template=template,
                        )
                        logger.info(f"Certificate created with number {certificate_number}")

                        # Save the generated certificate image
                        certificate.certificate_image.save(f"{certificate_number}.png", certificate_image)
                        logger.info(f"Certificate image saved for certificate {certificate_number}")

                        # Update enrollment status
                        enrollment.status = 'COMPLETED'
                        enrollment.completion_date = timezone.now()
                        enrollment.save()
                        logger.info(f"Enrollment {enrollment.id} status updated to COMPLETED")

                        # Create issuance log
                        CertificateIssuanceLog.objects.create(
                            certificate=certificate,
                            issued_by=issued_by,
                            ip_address=ip_address,
                            user_agent=user_agent
                        )
                        logger.info(f"Issuance log created for certificate {certificate_number}")

                        return certificate
                    except Exception as e:
                        logger.error(f"Error during certificate creation process: {str(e)}")
                        raise
                else:
                    logger.warning(f"Not all learning resources completed for enrollment {enrollment.id}. Certificate not issued.")
                return None
        except Exception as e:
            logger.error(f"Unexpected error during certificate issuance: {str(e)}")
            return None

    @classmethod
    def generate_certificate_image(cls, user_name, course_name, certificate_number, template):
        try:
            with Image.open(template.template_file.path) as img:
                draw = ImageDraw.Draw(img)

                # Load fonts (adjust paths as necessary)
                user_name_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'Roboto-Medium.ttf'), 120)
                course_name_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'Roboto-Regular.ttf'), 80)
                cert_number_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'Roboto-Regular.ttf'), 40)

                # Center and draw user name
                user_name_position = cls.center_text(draw, user_name, user_name_font, (540, 720), (1480, 770))
                draw.text(user_name_position, user_name, font=user_name_font, fill=(0, 0, 0))

                # Center and draw course name
                course_name_position = cls.center_text(draw, course_name, course_name_font, (540, 1000), (1480, 1050))
                draw.text(course_name_position, course_name, font=course_name_font, fill=(0, 0, 0))

                # Draw certificate number (not centered, keeping it at a fixed position)
                draw.text((100, 1400), f"Certificate Number: {certificate_number}", font=cert_number_font, fill=(0, 0, 0))

                # Save the image to a bytes buffer
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                return ContentFile(buffer.getvalue())
        except FileNotFoundError:
            logger.error(f"Certificate template file not found: {template.template_file.path}")
            raise
        except IOError:
            logger.error(f"Error reading certificate template file: {template.template_file.path}")
            raise

    @staticmethod
    def center_text(draw, text, font, point_a, point_b):
        text_width = draw.textlength(text, font=font)
        available_width = point_b[0] - point_a[0]
        start_x = point_a[0] + (available_width - text_width) / 2
        return (start_x, point_a[1])

    def revoke(self, revoked_by, reason):
        self.is_valid = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revocation_reason = reason
        self.save()

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False

class CertificateTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_file = models.FileField(upload_to='certificate_templates/')
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other templates as non-default
            CertificateTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class CertificateIssuanceLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='issuance_logs')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Issuance Log for {self.certificate.certificate_number}"