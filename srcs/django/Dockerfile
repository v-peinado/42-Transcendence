FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn pyotp==2.8.0

# Copiar el código de la aplicación (el propio proyecto que se ha creado)
COPY . .

# Copiar y dar permisos al script de entrada
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Iniciar la aplicación
CMD ["python", "django-entrypoint.py"]
