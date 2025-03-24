FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y \
	postgresql-client \
	libpq-dev \
	openssl \
	&& pip install --no-cache-dir -r requirements.txt \
	&& pip install --no-cache-dir gunicorn pyotp==2.8.0 \
	&& mkdir -p /app/logs \
	&& chmod 777 /app/logs

# Create celery user and setup directories with proper permissions
RUN adduser --disabled-password --gecos '' celeryuser \
	&& mkdir -p /var/lib/celery /var/run/celery /var/log/celery /home/celeryuser/.postgresql /home/celeryuser/.pg \
	&& chown -R celeryuser:celeryuser /var/lib/celery /var/run/celery /var/log/celery /home/celeryuser \
	&& chmod 755 /var/lib/celery /var/run/celery /var/log/celery \
	&& mkdir -p /root/.postgresql \
	&& chmod 755 /root/.postgresql

# Copy application files
COPY . .
COPY django-entrypoint.py /app/

RUN chmod +x /app/django-entrypoint.py && \
	chown -R celeryuser:celeryuser /app

# Setup entry script
ENV USE_DAPHNE=True

# Set default command
CMD ["python", "django-entrypoint.py"]
