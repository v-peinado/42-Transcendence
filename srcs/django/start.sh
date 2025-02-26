#!/bin/bash

# Crear directorio para archivos estáticos personalizados
mkdir -p /app/static_custom

# Ejecutar migraciones
python manage.py makemigrations
python manage.py makemigrations authentication
python manage.py makemigrations chat
python manage.py makemigrations tournament
python manage.py makemigrations game
python manage.py migrate

# Limpiar y recolectar archivos estáticos
rm -rf /app/static/*
python manage.py collectstatic --noinput --clear

# Crear directorio para celerybeat y asignar permisos
mkdir -p /var/lib/celery
chown -R celeryuser:celeryuser /var/lib/celery

# Establecer variable de entorno para el archivo de schedule
export CELERYBEAT_SCHEDULE_FILENAME=/var/lib/celery/celerybeat-schedule

# Iniciar Celery worker como celeryuser
su -m celeryuser -c "celery -A main worker --loglevel=info" &

# Iniciar Celery beat como celeryuser
su -m celeryuser -c "celery -A main beat --loglevel=info --schedule=/var/lib/celery/celerybeat-schedule" &

# Iniciar Daphne
daphne -b 0.0.0.0 -p 8000 main.asgi:application
