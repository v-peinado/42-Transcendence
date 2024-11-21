FROM nginx:alpine

# Instalar OpenSSL
RUN apk add --no-cache openssl

# Crear un usuario no root
RUN adduser -D -u 1000 nginxuser

# Crear directorios necesarios
RUN mkdir -p /tmp/ssl /tmp/client_temp \
    /tmp/proxy_temp_path \
    /tmp/fastcgi_temp \
    /tmp/uwsgi_temp \
    /tmp/scgi_temp \
    /etc/nginx/ssl

# Copiar script de generación de SSL y darle permisos
COPY ./ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh
RUN chmod +x /docker-entrypoint.d/20-generate-ssl.sh

# Copiar la configuración de nginx y los archivos del frontend
COPY nginx.conf /etc/nginx/nginx.conf
COPY frontend /usr/share/nginx/html

# Establecer permisos
RUN chown -R nginxuser:nginxuser /tmp && \
    chmod -R 755 /tmp && \
    chown -R nginxuser:nginxuser /usr/share/nginx/html && \
    chown -R nginxuser:nginxuser /var/cache/nginx && \
    chown -R nginxuser:nginxuser /var/log/nginx && \
    chown -R nginxuser:nginxuser /etc/nginx/ssl && \
    chown -R nginxuser:nginxuser /docker-entrypoint.d && \
    touch /var/run/nginx.pid && \
    chown -R nginxuser:nginxuser /var/run/nginx.pid

USER nginxuser

EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]