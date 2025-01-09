FROM owasp/modsecurity-crs:nginx

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
        modsecurity-crs && \
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
    touch /var/log/vault/audit.log && \
    chmod 750 /etc/vault.d/data && \
    chmod -R 755 /var/log/vault && \
    chmod 640 /var/log/vault/audit.log && \
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

ENV MODSECURITY=On \
    VAULT_ADDR=https://127.0.0.1:8200 \
    VAULT_SKIP_VERIFY=true \
    PATH="${PATH}:/usr/local/bin"

EXPOSE 8081 8200 8444

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

CMD ["/bin/bash", "-c", "/usr/local/bin/init-vault.sh & nginx -g 'daemon off;'"]