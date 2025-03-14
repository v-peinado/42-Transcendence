from celery import shared_task
from authentication.services.cleanup_service import CleanupService
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_inactive_users():
    """
    Celery task to clean up inactive users
    This task runs according to TASK_CHECK_INTERVAL (in settings.py)
    """
    try:
        logger.info("🔄 ====== STARTING CLEANUP TASK ======")
        result = CleanupService.cleanup_inactive_users()
        logger.info(f"✅ Task completed - Processing complete")
        logger.info("======= END OF CLEANUP TASK =======\n")
    except Exception as e:
        logger.error(f"❌ Task failed: {str(e)}")
        logger.info("======= END OF CLEANUP TASK =======\n")
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