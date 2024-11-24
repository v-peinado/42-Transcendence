# Usa la imagen oficial de Python como base
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copiar requirements primero 
COPY requirements.txt .

# Instalar dependencias con --no-cache-dir para forzar reinstalación
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn pyotp==2.8.0

# Copiar el resto de archivos
COPY . .

# Copiar y configurar el script de entrada
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Comando para ejecutar el script
CMD ["python", "django-entrypoint.py"]
