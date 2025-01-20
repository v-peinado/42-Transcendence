FROM owasp/modsecurity-crs:nginx

# Configuración de la imagen
USER root
WORKDIR /app

ARG VAULT_VERSION=1.13.0

# Instalar dependencias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        unzip \
        openssl \
        libmodsecurity3 \
        modsecurity-crs \
        netcat-traditional && \
    curl -fsSL https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip -o vault.zip && \
    unzip vault.zip && \
    mv vault /usr/local/bin/ && \
    rm vault.zip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Crear directorios base
RUN mkdir -p \
    /var/log/modsecurity \
    /var/log/vault \
    /etc/vault.d/data \
    /var/run/nginx \
    /tmp/ssl \
    /tmp/modsecurity/{data,tmp} \
    /etc/nginx/modsecurity.d \
    /etc/nginx/modsecurity/rules \
    /etc/modsecurity/crs

# Crear usuario
RUN useradd -r -s /sbin/nologin nginxuser || true

# Copiar archivos de configuración
COPY waf/vault/config.hcl /etc/vault.d/
COPY waf/vault/init-vault.sh /usr/local/bin/
COPY waf/custom-nginx.conf /etc/nginx/nginx.conf
COPY ssl/generate-ssl.sh /usr/local/bin/
COPY ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh
COPY waf/modsecurity/modsecurity.conf /etc/nginx/modsecurity.d/
COPY waf/modsecurity/rules/ /etc/nginx/modsecurity/rules/
COPY waf/modsecurity/crs-setup.conf /etc/modsecurity/crs/crs-setup.conf

# Configurar permisos y enlaces
RUN chown -R nginxuser:nginxuser \
        /var/log/modsecurity \
        /etc/vault.d \
        /var/log/vault \
        /var/run/nginx \
        /tmp/ssl \
        /tmp/modsecurity \
        /etc/nginx/modsecurity.d \
        /etc/nginx/modsecurity && \
    chmod 755 /etc/vault.d && \
    chmod 750 /etc/vault.d/data && \
    chmod -R 755 /var/log/vault && \
    touch /var/log/vault/audit.log && \
    chmod 640 /var/log/vault/audit.log && \
    chown -R nginxuser:nginxuser /var/log/vault/audit.log && \
    chmod +x \
        /usr/local/bin/generate-ssl.sh \
        /usr/local/bin/init-vault.sh \
        /docker-entrypoint.d/20-generate-ssl.sh && \
    ln -sf /etc/nginx/modsecurity/rules/main.conf /etc/nginx/modsecurity.d/main.conf && \
    ln -sf /etc/modsecurity/crs/crs-setup.conf /usr/share/modsecurity-crs/crs-setup.conf && \
    chmod -R 644 \
        /etc/nginx/modsecurity.d/* \
        /etc/nginx/modsecurity/rules/* \
        /etc/modsecurity/crs/* && \
    /usr/local/bin/generate-ssl.sh

# Variables de entorno
ENV MODSECURITY=On \
    VAULT_ADDR=http://127.0.0.1:8200 \
    VAULT_SKIP_VERIFY=true \
    PATH="${PATH}:/usr/local/bin"

# Exponer puertos de la aplicación
EXPOSE 8081 8200 8444

# HEALTHCHECK para el contenedor
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f -k https://localhost:8444/health || exit 1

# Comando de inicio
CMD ["sh", "-c", "/usr/local/bin/init-vault.sh && nginx -g 'daemon off;'"]