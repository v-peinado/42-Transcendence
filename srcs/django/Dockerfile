# Usa la imagen oficial de Python como base
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del proyecto
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copia los archivos del proyecto
COPY . .

# Comando para ejecutar el servidor
CMD ["gunicorn", "main.wsgi:application", "--bind", "0.0.0.0:8000"]
