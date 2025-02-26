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

# To see celery tasks in action:

# 1. Create a new user

# 2. Run the Celery worker: in a terminal:
#	docker exec -it srcs-web-1 celery -A main worker -l INFO

# 3. Run the Celery beat scheduler: in a new terminal:
#	docker exec -it srcs-web-1 celery -A main beat -l INFO

# 4. Trigger the task: in a new terminal:
#	docker exec -it srcs-web-1 python manage.py shell
#	from authentication.tasks import cleanup_inactive_users
#	cleanup_inactive_users.delay()

# 5. Check logs in the worker terminal

# 6. Check the database to see if the user was deleted