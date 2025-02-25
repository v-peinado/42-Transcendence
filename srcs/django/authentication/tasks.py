from celery import shared_task
from .services.gdpr_service import GDPRService
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_inactive_users():
    """
    Celery task to clean up inactive users
    This task is scheduled to run daily through CELERY_BEAT_SCHEDULE in settings.py
    """
    try:
        logger.info("Starting inactive users cleanup task")
        GDPRService.cleanup_inactive_users()
        logger.info("Inactive users cleanup task completed successfully")
    except Exception as e:
        logger.error(f"Error in cleanup_inactive_users task: {str(e)}")
        raise
    
# Tasks are used to perform background operations in Django. 
# They are defined as functions and are executed by the Celery worker. 
# In this case, the cleanup_inactive_users task is used to remove users who have been inactive for more than 60 days. 
# The task is scheduled to run daily through the CELERY_BEAT_SCHEDULE setting in settings.py. 
# The task calls the cleanup_inactive_users method from the GDPRService class, which handles the deletion of inactive users. 
# The task logs information about the cleanup process and any errors that occur. 
# If an error occurs, it is logged and raised to the caller.
