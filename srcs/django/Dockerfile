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

# Crear un usuario no-root para celery
RUN adduser --disabled-password --gecos '' celeryuser

# Asegurar que los directorios necesarios tengan los permisos correctos
RUN mkdir -p /var/run/celery /var/log/celery \
	&& chown -R celeryuser:celeryuser /var/run/celery /var/log/celery

# Create celery directories with proper permissions
RUN mkdir -p /var/lib/celery /var/run/celery /var/log/celery && \
	chown -R celeryuser:celeryuser /var/lib/celery /var/run/celery /var/log/celery && \
	chmod 755 /var/lib/celery /var/run/celery /var/log/celery

COPY . .
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Set proper permissions for app directory
RUN chown -R celery:celery /app

# Add supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Crear script de entrada
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Cambiar el CMD para usar el script
CMD ["/app/start.sh"]
