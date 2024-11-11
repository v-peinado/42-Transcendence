# Usa la imagen oficial de Python como base
FROM python:3.10-slim

RUN apt-get update && apt-get install -y libpq-dev

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos y el proyecto
COPY requirements.txt requirements.txt
COPY . .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto 8000
EXPOSE 8000

# Comando para ejecutar el servidor
CMD ["python", "django-entrypoint.py"]
