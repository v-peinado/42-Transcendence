from celery import shared_task
from django.conf import settings
from .services.gdpr_service import GDPRService
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_inactive_users():
    """
    Celery task to clean up inactive users
    This task runs according to TASK_CHECK_INTERVAL (in settings.py)
    """
    try:
        logger.info("Starting inactive users cleanup task")
        GDPRService.cleanup_inactive_users()
        logger.info("Inactive users cleanup task completed successfully")
    except Exception as e:
        logger.error(f"Error in cleanup_inactive_users task: {str(e)}")
        raise

# Configure task schedule (this is a Celery setting for periodic maintenance tasks)
# The cleanup_inactive_users task is scheduled to run daily (every 24 hours)
# The task is executed by the Celery worker (celery is in import statement)
CELERY_BEAT_SCHEDULE = {
    'cleanup-inactive-users': {
        'task': 'authentication.tasks.cleanup_inactive_users',
        'schedule': settings.TASK_CHECK_INTERVAL,
    },
}

    
# Tasks are used to perform background operations in Django. 
# They are defined as functions and are executed by the Celery worker. 
# The task is scheduled to run daily through the CELERY_BEAT_SCHEDULE setting in settings.py. 
# The task calls the cleanup_inactive_users method from the GDPRService class, which handles the deletion of inactive users. 
