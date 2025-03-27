from authentication.services.cleanup_service import CleanupService
from celery import shared_task
import logging
import os


# A task is a function that can be run asynchronously.
# To create a task, use the shared_task() decorator.
# The task is then registered by the worker (Celery) and can be executed later.

# Celery is a distributed task queue that is used to handle asynchronous tasks in Django web applications.

logger = logging.getLogger(__name__)

@shared_task # Decorator to make this a Celery task
def cleanup_inactive_users():
    """
    Celery task to clean up inactive users
    This task runs according to TASK_CHECK_INTERVAL (in settings.py)
    """
    try:
        logger.info("🔄 ====== STARTING CLEANUP TASK ======")
        
        # Verify database connection configuration
        celery_user = os.environ.get("CELERY_USER")
        if not celery_user:
            logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
            celery_user = "celeryuser"
        
        # Log all SSL-related environment variables
        ssl_vars = {
            "PGSSLMODE": os.environ.get("PGSSLMODE", "Not set"),
            "PGSSLCERT": os.environ.get("PGSSLCERT", "Not set"),
            "PGSSLKEY": os.environ.get("PGSSLKEY", "Not set"),
            "PGSSLROOTCERT": os.environ.get("PGSSLROOTCERT", "Not set"),
            "PGSERVICEFILE": os.environ.get("PGSERVICEFILE", "Not set"),
            "PGSERVICE": os.environ.get("PGSERVICE", "Not set"),
        }
        
        #logger.info(f"PostgreSQL SSL configuration: {ssl_vars}")
        
        # Check if PostgreSQL certificate exists
        cert_paths = [
            os.environ.get("PGSSLCERT", f"/home/{celery_user}/.postgresql/postgresql.crt"),
            f"/home/{celery_user}/.postgresql/postgresql.crt",
            "/root/.postgresql/postgresql.crt",
        ]
        
        # Check each path and permissions
        for path in cert_paths:
            exists = os.path.exists(path)
            readable = os.access(path, os.R_OK) if exists else False
            #logger.info(f"Certificate path {path}: exists={exists}, readable={readable}")
            
            if exists and readable:
                logger.info(f"Using PostgreSQL certificate: {path}")
                break
        
        # Override SSL mode to disable SSL if having issues
        # Uncomment for testing:
        # os.environ["PGSSLMODE"] = "disable"
        # logger.info("*** IMPORTANT: SSL has been DISABLED for debugging purposes ***")
        
        # Run the cleanup service
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