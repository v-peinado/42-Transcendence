from django.conf import settings
from celery import Celery
import os

# Set the default Django settings module for the 'celery' program.
# This is the same as the DJANGO_SETTINGS_MODULE environment variable 
# but we put it here to maintain the configuration in the same file.

# Celery 6.0 specific configuration (see https://docs.celeryproject.org/en/stable/whatsnew-6.0.html)

# Configure the environment for django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# Create the Celery application
app = Celery('main')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Security configuration
app.conf.update(**settings.CELERY_SECURITY_CONFIG)

# Worker configuration
app.conf.update(**settings.CELERY_WORKER_CONFIG)

# Aply the configuration for the beat
app.conf.update(**settings.CELERY_BEAT_CONFIG)

# Configure SSL settings for PostgreSQL connection
# Set the SSL connection parameters as environment variables for Celery workers
os.environ.setdefault('PGSSLMODE', 'require')
os.environ.setdefault('PGAPPNAME', 'celery_worker')

# Update Celery configuration with PostgreSQL options
app.conf.update(
    broker_connection_retry_on_startup=True,
    worker_enable_remote_control=False,
    worker_send_task_events=False,
    task_send_sent_event=False,
    worker_log_format='[%(asctime)s: %(levelname)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s] %(task_name)s - %(message)s',
    worker_redirect_stdouts_level='ERROR',
    database_engine_options={
        'sslmode': 'require',
        'application_name': 'celery_worker',
        'connect_timeout': 30,
    }
)

# Search for tasks in Django applications
app.autodiscover_tasks()

@app.task(bind=True) # app.task decorator to create a task from a regular function
def debug_task(self):
    print(f'Request: {self.request!r}')
