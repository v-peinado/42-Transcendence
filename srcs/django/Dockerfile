FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
	pip install --no-cache-dir gunicorn pyotp==2.8.0 && \
	mkdir -p /app/logs && \
	chmod 777 /app/logs

COPY . .
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Iniciar la aplicación
CMD ["python", "django-entrypoint.py"]
