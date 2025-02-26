FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y postgresql-client && \
	pip install --no-cache-dir -r requirements.txt && \
	pip install --no-cache-dir gunicorn pyotp==2.8.0 && \
	mkdir -p /app/logs && \
	chmod 777 /app/logs

# Install Supervisor
RUN apt-get update && apt-get install -y supervisor

# Create celery user and setup directories
RUN adduser --disabled-password --gecos '' celeryuser && \
	mkdir -p /var/lib/celery /var/run/celery /var/log/celery && \
	chown -R celeryuser:celeryuser /var/lib/celery /var/run/celery /var/log/celery && \
	chmod 755 /var/lib/celery /var/run/celery /var/log/celery

# Copy application files
COPY . .
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Set proper permissions for app directory
RUN chown -R celeryuser:celeryuser /app

# Add supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Setup entry script
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Set default command
CMD ["/app/start.sh"]
