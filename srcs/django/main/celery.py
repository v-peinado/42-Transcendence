import os
from celery import Celery
from django.conf import settings

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

# Configuración específica para Celery 6.0
app.conf.update(
    broker_connection_retry_on_startup=True,
    worker_enable_remote_control=False,
    worker_send_task_events=False,
    task_send_sent_event=False,
    worker_log_format='[%(asctime)s: %(levelname)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s] %(task_name)s - %(message)s',
    worker_redirect_stdouts_level='ERROR',
)

# Search for tasks in Django applications
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
