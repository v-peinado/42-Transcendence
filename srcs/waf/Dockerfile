FROM owasp/modsecurity-crs:nginx

USER root

WORKDIR /app

# Instalar HashiCorp Vault y dependencias
RUN apt-get update && \
    apt-get install -y curl unzip openssl && \
    curl -fsSL https://releases.hashicorp.com/vault/1.13.0/vault_1.13.0_linux_amd64.zip -o vault.zip && \
    unzip vault.zip && \
    mv vault /usr/local/bin/ && \
    rm vault.zip

# Crear directorios y configurar permisos
RUN mkdir -p /var/log/modsecurity \
            /etc/vault.d/data \
            /etc/modsecurity/rules \
            /var/log/vault \
            /var/run/nginx \
            /tmp/ssl \
            /tmp/modsecurity/data && \
    useradd -r -s /sbin/nologin nginxuser || true && \
    chown -R nginxuser:nginxuser \
        /var/log/modsecurity \
        /etc/vault.d \
        /etc/modsecurity/rules \
        /var/log/vault \
        /var/run/nginx \
        /tmp/ssl \
        /tmp/modsecurity

RUN mkdir -p /tmp/ssl && \
    chown -R nginxuser:nginxuser /tmp/ssl

# Copiar archivos de configuración
COPY ./rules/ /etc/modsecurity/rules/
COPY ./vault/config.hcl /etc/vault.d/
COPY ./init-vault.sh /usr/local/bin/
COPY ./ssl/generate-ssl.sh /usr/local/bin/
COPY ./custom-nginx.conf /etc/nginx/nginx.conf

COPY ./ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh
RUN chmod +x /docker-entrypoint.d/20-generate-ssl.sh

RUN chown -R nginxuser:nginxuser /etc/modsecurity/rules

# Establecer permisos de ejecución
RUN chmod +x /usr/local/bin/init-vault.sh /usr/local/bin/generate-ssl.sh

# Generar certificados SSL
RUN /usr/local/bin/generate-ssl.sh

# Variables de entorno
ENV MODSECURITY=On
ENV MODSECURITY_AUDIT_ENGINE=On
ENV MODSECURITY_AUDIT_LOG=/var/log/modsecurity/audit.log
ENV MODSECURITY_AUDIT_LOG_FORMAT=JSON
ENV VAULT_ADDR=http://127.0.0.1:8200
ENV PATH="${PATH}:/usr/local/bin"
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx/conf.d

# Crear punto de montaje
VOLUME ["/etc/vault.d/data", "/var/log/modsecurity"]

# Mantener root como usuario para el inicio
USER root

# Exponer puertos necesarios
EXPOSE 80 443 8200 8201

# Comando de inicio
CMD ["/bin/bash", "-c", "/usr/local/bin/init-vault.sh & nginx -g 'daemon off;'"]