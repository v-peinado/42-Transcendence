FROM owasp/modsecurity-crs:nginx

USER root
WORKDIR /app

# Instalar HashiCorp Vault y dependencias
RUN apt-get update && \
    apt-get install -y curl unzip openssl libmodsecurity3 modsecurity-crs && \
    curl -fsSL https://releases.hashicorp.com/vault/1.13.0/vault_1.13.0_linux_amd64.zip -o vault.zip && \
    unzip vault.zip && \
    mv vault /usr/local/bin/ && \
    rm vault.zip

# Crear directorios y configurar permisos
RUN mkdir -p \
    /var/log/modsecurity \
    /etc/vault.d/data \
    /var/log/vault \
    /var/run/nginx \
    /tmp/ssl \
    /tmp/modsecurity/{data,tmp} \
    /etc/nginx/modsecurity.d \
    /etc/nginx/modsecurity/rules && \
    useradd -r -s /sbin/nologin nginxuser || true && \
    chown -R nginxuser:nginxuser \
    /var/log/modsecurity \
    /etc/vault.d \
    /var/log/vault \
    /var/run/nginx \
    /tmp/ssl \
    /tmp/modsecurity \
    /etc/nginx/modsecurity.d \
    /etc/nginx/modsecurity

# Copiar archivos de configuración
COPY waf/vault/config.hcl /etc/vault.d/
COPY waf/vault/init-vault.sh /usr/local/bin/
COPY waf/custom-nginx.conf /etc/nginx/nginx.conf
COPY ssl/generate-ssl.sh /usr/local/bin/
COPY ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh

# ModSecurity setup
COPY waf/modsecurity/modsecurity.conf /etc/nginx/modsecurity.d/
COPY waf/modsecurity/rules/ /etc/nginx/modsecurity/rules/
COPY waf/modsecurity/crs-setup.conf /etc/modsecurity/crs/crs-setup.conf

RUN mkdir -p /etc/modsecurity/crs && \
    ln -sf /etc/nginx/modsecurity/rules/main.conf /etc/nginx/modsecurity.d/main.conf && \
    ln -sf /etc/modsecurity/crs/crs-setup.conf /usr/share/modsecurity-crs/crs-setup.conf && \
    chown -R nginx:nginx \
        /etc/nginx/modsecurity.d \
        /etc/nginx/modsecurity/rules \
        /etc/modsecurity/crs && \
    chmod -R 644 \
        /etc/nginx/modsecurity.d/* \
        /etc/nginx/modsecurity/rules/* \
        /etc/modsecurity/crs/*

# Configurar permisos finales
RUN chmod +x \
    /docker-entrypoint.d/20-generate-ssl.sh \
    /usr/local/bin/init-vault.sh \
    /usr/local/bin/generate-ssl.sh && \
    /usr/local/bin/generate-ssl.sh

ENV MODSECURITY=On \
    VAULT_ADDR=http://127.0.0.1:8200 \
    PATH="${PATH}:/usr/local/bin"

EXPOSE 8081 8200 8444 

CMD ["/bin/bash", "-c", "/usr/local/bin/init-vault.sh & nginx -g 'daemon off;'"]
