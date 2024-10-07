import logging
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import DeliveryEmailTemplate, Enrollment, DeliveryInstructor

User = get_user_model()

logger = logging.getLogger(__name__)

def send_delivery_email(delivery, email_type):
    logger.info(f"Sending {email_type} emails for delivery {delivery.id}")
    try:
        template = DeliveryEmailTemplate.objects.get(delivery=delivery, email_type=email_type)
        email_body = Template(template.body)

        # Get enrolled users
        enrollments = Enrollment.objects.filter(delivery=delivery)
        
        # Get instructors
        instructors = DeliveryInstructor.objects.filter(delivery=delivery)

        recipients = list(enrollments.values_list('user__email', flat=True)) + list(instructors.values_list('instructor__email', flat=True))
        logger.info(f"Recipients for {email_type} email: {recipients}")

        for recipient in recipients:
            user = User.objects.get(email=recipient)
            context = Context({
                'participant_name': user.get_full_name(),
                'delivery_title': delivery.title,
                'delivery_type': delivery.get_delivery_type_display(),
                'start_date': delivery.start_date,
                'end_date': delivery.end_date,
                'organization_name': user.current_organization.name if user.current_organization else "Our Organization",
            })
            
            rendered_email = email_body.render(context)
            
            send_mail(
                subject=f"{delivery.title} - {email_type.replace('_', ' ').title()}",
                message=rendered_email,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        
        logger.info(f"Successfully sent {email_type} emails for delivery {delivery.id}")
    except DeliveryEmailTemplate.DoesNotExist:
        logger.error(f"Email template for {email_type} not found for delivery {delivery.id}")
    except Exception as e:
        logger.error(f"Error sending {email_type} emails for delivery {delivery.id}: {str(e)}")