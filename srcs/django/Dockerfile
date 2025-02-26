FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y postgresql-client && \
	pip install --no-cache-dir -r requirements.txt && \
	pip install --no-cache-dir gunicorn pyotp==2.8.0 && \
	mkdir -p /app/logs && \
	chmod 777 /app/logs

# Install Supervisor to manage multiple processes
RUN apt-get update && apt-get install -y supervisor

# Create celery user and group
RUN groupadd -r celery && useradd -r -g celery celery

# Create necessary directories with proper permissions
RUN mkdir -p /var/run/celery /var/log/celery /var/lib/celery && \
	chown -R celery:celery /var/run/celery /var/log/celery /var/lib/celery

COPY . .
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Set proper permissions for app directory
RUN chown -R celery:celery /app

# Add supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Change entrypoint to use supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
