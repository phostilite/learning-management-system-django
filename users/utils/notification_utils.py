# users/utils/notification_utils.py

from activities.models import ActivityLog, SystemNotification
import logging

logger = logging.getLogger(__name__)

def create_notification(user, message, notification_type='INFO'):
    try:
        SystemNotification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type
        )
    except Exception as e:
        logger.error(f"Error creating notification for user {user.username}: {str(e)}")

def log_activity(user, action_type, description):
    try:
        ActivityLog.objects.create(
            user=user,
            action_type=action_type,
            description=description
        )
    except Exception as e:
        logger.error(f"Error logging activity for user {user.username}: {str(e)}")