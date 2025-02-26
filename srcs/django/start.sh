#!/bin/bash

# Wait for Vault secrets to be loaded
while [ ! -f /tmp/ssl/django_token ]; do
    echo "Waiting for Vault token..."
    sleep 2
done

# Verify required system user exists before starting services
if ! id -u "${CELERY_USER}" >/dev/null 2>&1; then
    echo "Error: Required system user not found"
    exit 1
fi

echo "Info: Required system user verified successfully"

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

# Create directories for celery with minimal logging
echo "Info: Setting up Celery environment..."
mkdir -p /var/lib/celery
chown -R "${CELERY_USER}":"${CELERY_USER}" /var/lib/celery

# Environment variables for Celery 
export CELERYBEAT_SCHEDULE_FILENAME=/var/lib/celery/celerybeat-schedule

# Initialize Celery services
echo "Info: Starting Celery services..."
su -m "${CELERY_USER}" -c "celery -A main worker --loglevel=info" &
su -m "${CELERY_USER}" -c "celery -A main beat --loglevel=info --schedule=/var/lib/celery/celerybeat-schedule" &

# Start Daphne server
daphne -b 0.0.0.0 -p 8000 main.asgi:application
