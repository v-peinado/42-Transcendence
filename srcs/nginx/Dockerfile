FROM nginx:alpine

WORKDIR /app

# Crear un usuario no root
RUN adduser -D -u 1000 nginxuser

# Copiar la configuración de nginx y los archivos del frontend
COPY nginx.conf /etc/nginx/nginx.conf
COPY frontend /usr/share/nginx/html

# Crear directorios temporales con permisos correctos
RUN mkdir -p /tmp/client_temp \
    /tmp/proxy_temp_path \
    /tmp/fastcgi_temp \
    /tmp/uwsgi_temp \
    /tmp/scgi_temp && \
    chown -R nginxuser:nginxuser /tmp && \
    chmod -R 755 /tmp && \
    chown -R nginxuser:nginxuser /usr/share/nginx/html && \
    chown -R nginxuser:nginxuser /var/cache/nginx && \
    chown -R nginxuser:nginxuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginxuser:nginxuser /var/run/nginx.pid

# Cambiar al usuario no root
USER nginxuser

# Exponer el puerto 80
EXPOSE 80

# Comando para iniciar nginx
CMD ["nginx", "-g", "daemon off;"]