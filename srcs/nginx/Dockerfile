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
    apt-get install -y openssl && \
    mkdir -p /var/log/modsecurity \
        /tmp/ssl \
        /tmp/client_temp \
        /tmp/proxy_temp_path \
        /tmp/fastcgi_temp \
        /tmp/uwsgi_temp \
        /tmp/scgi_temp \
        /etc/nginx/ssl \
        /etc/modsecurity/rules && \
    chown -R nginx:nginx \
        /var/log/modsecurity \
        /tmp/ssl \
        /tmp/client_temp \
        /tmp/proxy_temp_path \
        /tmp/fastcgi_temp \
        /tmp/uwsgi_temp \
        /tmp/scgi_temp \
        /etc/nginx \
        /var/cache/nginx \
        /var/log/nginx \
        /usr/share/nginx/html \
        /usr/bin/openssl \
        /etc/modsecurity/rules && \
    chmod -R 755 /etc/nginx \
        /var/cache/nginx \
        /var/log/nginx \
        /usr/share/nginx/html \
        /usr/bin/openssl

# Crear el usuario nginx si no existe
RUN useradd -r -s /sbin/nologin nginx || true

# Copiar la configuración de nginx y los archivos del frontend
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/templates /etc/nginx/templates
COPY nginx/frontend /usr/share/nginx/html
COPY ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh

# Establecer permisos para el script
RUN chmod +x /docker-entrypoint.d/20-generate-ssl.sh && \
    chown -R nginx:nginx /docker-entrypoint.d/20-generate-ssl.sh

EXPOSE 8080 8443

# No cambiar al usuario nginx para permitir que el entrypoint se ejecute como root
CMD ["nginx", "-g", "daemon off;"]