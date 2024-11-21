# Usa la imagen oficial de Python como base
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copia los archivos del proyecto
COPY . .

# Copiar y configurar el script de entrada (usar .py en lugar de .sh)
COPY django-entrypoint.py /app/
RUN chmod +x /app/django-entrypoint.py

# Comando para ejecutar el script
CMD ["python", "django-entrypoint.py"]
