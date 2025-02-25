from celery import shared_task
from celery.schedules import schedule
from django.conf import settings
from .services.gdpr_service import GDPRService
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_inactive_users():
    """
    Celery task to clean up inactive users
    This task runs according to TASK_CHECK_INTERVAL setting
    """
    try:
        logger.info("Starting inactive users cleanup task")
        GDPRService.cleanup_inactive_users()
        logger.info("Inactive users cleanup task completed successfully")
    except Exception as e:
        logger.error(f"Error in cleanup_inactive_users task: {str(e)}")
        raise

# Configure task schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-inactive-users': {
        'task': 'authentication.tasks.cleanup_inactive_users',
        'schedule': settings.TASK_CHECK_INTERVAL,
    },
}
