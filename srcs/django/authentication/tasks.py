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

# 1. Create a new user:
# Open a terminal and run the following commands:

	# docker exec -it srcs-web-1 python manage.py shell

	# from django.utils import timezone
	# from authentication.models import CustomUser
	# from datetime import timedelta

	# user = CustomUser.objects.create_user(
	#     username='test_celery',
	#     email='test@celery.com',
	#     password='test123'
	# )
	# user.email_verified = True
	# user.is_active = True
	# user.last_login = timezone.now() - timedelta(seconds=70)  # Más del umbral de 60 segundos
	# user.inactivity_notified = True
	# user.inactivity_notification_date = timezone.now() - timedelta(seconds=20)  # Pasado el período de advertencia
	# user.save()

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