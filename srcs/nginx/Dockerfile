FROM owasp/modsecurity-crs:nginx

# Primero nos aseguramos de ser root para todas las operaciones
USER root

# Variables de entorno para ModSecurity
ENV MODSECURITY=On
ENV MODSECURITY_AUDIT_ENGINE=On
ENV MODSECURITY_AUDIT_LOG=/var/log/modsecurity/audit.log
ENV MODSECURITY_AUDIT_LOG_FORMAT=JSON

# Actualizar e instalar OpenSSL
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y openssl

# Crear el usuario nginx si no existe
RUN useradd -r -s /sbin/nologin nginx || true

# Crear directorios y establecer permisos
RUN mkdir -p /var/log/modsecurity \
    /tmp/ssl \
    /tmp/client_temp \
    /tmp/proxy_temp_path \
    /tmp/fastcgi_temp \
    /tmp/uwsgi_temp \
    /tmp/scgi_temp \
    /etc/nginx/ssl && \
    chown -R nginx:nginx \
        /var/log/modsecurity \
        /tmp/ssl \
        /tmp/client_temp \
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

# Establecer permisos finales
RUN chown -R nginx:nginx \
    /var/cache/nginx \
    /var/log/nginx \
    /usr/share/nginx/html \
    /docker-entrypoint.d && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]