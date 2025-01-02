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

# Crear directorios y configurar permisos (consolidado)
RUN mkdir -p \
        /var/log/modsecurity \
        /etc/vault.d/data \
        /var/log/vault \
        /var/run/nginx \
        /tmp/ssl \
        /tmp/modsecurity/data && \
    useradd -r -s /sbin/nologin nginxuser || true && \
    chown -R nginxuser:nginxuser \
        /var/log/modsecurity \
        /etc/vault.d \
        /var/log/vault \
        /var/run/nginx \
        /tmp/ssl \
        /tmp/modsecurity

# Copiar archivos de configuración
COPY ./vault/config.hcl /etc/vault.d/
COPY ./init-vault.sh /usr/local/bin/
COPY ./ssl/generate-ssl.sh /usr/local/bin/
COPY ./custom-nginx.conf /etc/nginx/nginx.conf
COPY ./ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh

# Configurar permisos
RUN chmod +x \
    /docker-entrypoint.d/20-generate-ssl.sh \
    /usr/local/bin/init-vault.sh \
    /usr/local/bin/generate-ssl.sh && \
    /usr/local/bin/generate-ssl.sh

# Variables de entorno esenciales
ENV MODSECURITY=On \
    VAULT_ADDR=http://127.0.0.1:8200 \
    PATH="${PATH}:/usr/local/bin"

EXPOSE 8081 8200 8444 

CMD ["/bin/bash", "-c", "/usr/local/bin/init-vault.sh & nginx -g 'daemon off;'"]