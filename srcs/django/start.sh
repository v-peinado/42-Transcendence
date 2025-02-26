#!/bin/bash

# Create directories for static files
mkdir -p /app/static_custom

python manage.py makemigrations
python manage.py makemigrations authentication
python manage.py makemigrations chat
python manage.py makemigrations tournament
python manage.py makemigrations game
python manage.py migrate

# Clear static files and collect new ones (to avoid conflicts)
rm -rf /app/static/*
python manage.py collectstatic --noinput --clear

# Create directories for celery
mkdir -p /var/lib/celery
chown -R celeryuser:celeryuser /var/lib/celery

# Environment variables for Celery 
export CELERYBEAT_SCHEDULE_FILENAME=/var/lib/celery/celerybeat-schedule

# Initialize Celery as celeryuser
su -m celeryuser -c "celery -A main worker --loglevel=info" &

# Initialize Celery Beat as celeryuser
su -m celeryuser -c "celery -A main beat --loglevel=info --schedule=/var/lib/celery/celerybeat-schedule" &

# Start Daphne server
daphne -b 0.0.0.0 -p 8000 main.asgi:application
