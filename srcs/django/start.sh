#!/bin/bash

# Debug info
echo "Debug: CELERY_USER=${CELERY_USER}"
echo "Debug: Checking if user exists..."
id "${CELERY_USER}" || (echo "Error: User ${CELERY_USER} does not exist" && exit 1)

# Check if CELERY_USER is set
if [ -z "${CELERY_USER}" ]; then
    echo "Error: CELERY_USER environment variable is not set"
    exit 1
fi

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

# Create directories for celery with debug info
echo "Debug: Creating celery directories..."
mkdir -p /var/lib/celery
echo "Debug: Setting permissions for ${CELERY_USER}..."
chown -R ${CELERY_USER}:${CELERY_USER} /var/lib/celery
ls -la /var/lib/celery

# Environment variables for Celery 
export CELERYBEAT_SCHEDULE_FILENAME=/var/lib/celery/celerybeat-schedule

# Initialize Celery as CELERY_USER
su -m ${CELERY_USER} -c "celery -A main worker --loglevel=info" &

# Initialize Celery Beat as CELERY_USER
su -m ${CELERY_USER} -c "celery -A main beat --loglevel=info --schedule=/var/lib/celery/celerybeat-schedule" &

# Start Daphne server
daphne -b 0.0.0.0 -p 8000 main.asgi:application
