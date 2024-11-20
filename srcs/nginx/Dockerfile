FROM nginx:alpine

WORKDIR /app

# Crear un usuario no root
RUN adduser -D -u 1000 nginxuser

# Copiar la configuración de nginx y los archivos del frontend
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend /usr/share/nginx/html

# Cambiar los permisos para que el usuario no root pueda acceder
RUN chown -R nginxuser:nginxuser /usr/share/nginx/html && \
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