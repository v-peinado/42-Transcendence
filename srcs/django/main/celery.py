import os
from celery import Celery
import logging
from logging.handlers import RotatingFileHandler

# Configure the environment for django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# Create the Celery application
app = Celery('main')

# Config redis as broker and result backend
app.conf.broker_url = 'redis://redis:6379/0'
app.conf.result_backend = 'redis://redis:6379/0'

# Configure Celery app with proper scheduler file location
app.conf.update(
    beat_schedule_filename='/var/lib/celery/celerybeat-schedule',
    broker_connection_retry_on_startup=True  # Fix deprecation warning
)

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure logging for Celery to use same handler as Django
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Get both loggers and configure them
celery_logger = logging.getLogger('celery')
django_logger = logging.getLogger('django')

celery_logger.addHandler(console_handler)
django_logger.addHandler(console_handler)

celery_logger.setLevel(logging.INFO)
django_logger.setLevel(logging.INFO)

# Ensure the loggers propagate to the root logger
celery_logger.propagate = True
django_logger.propagate = True

# Search for tasks in Django applications
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
