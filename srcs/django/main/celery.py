import os
from celery import Celery

# Configura las variables de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# Crea la aplicación Celery
app = Celery('main')

# Configuración usando Redis como broker
app.conf.broker_url = 'redis://redis:6379/0'
app.conf.result_backend = 'redis://redis:6379/0'

# Carga la configuración desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Busca tareas en todas las aplicaciones Django registradas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
