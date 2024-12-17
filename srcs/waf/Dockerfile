FROM owasp/modsecurity-crs:nginx

USER root

WORKDIR /app

# Instalar HashiCorp Vault y dependencias usando apt-get
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -fsSL https://releases.hashicorp.com/vault/1.13.0/vault_1.13.0_linux_amd64.zip -o vault.zip && \
    unzip vault.zip && \
    mv vault /usr/local/bin/ && \
    rm vault.zip

# Crear usuario WAF y directorios necesarios
RUN useradd -r -s /sbin/nologin nginxuser || true && \
    mkdir -p /var/log/modsecurity /etc/vault.d/data /etc/modsecurity/rules && \
    chown -R nginxuser:nginxuser /var/log/modsecurity /etc/vault.d /etc/modsecurity/rules && \
    chmod -R 777 /var/log/modsecurity /etc/vault.d /etc/modsecurity/rules

# Variables de entorno
ENV MODSECURITY=On
ENV MODSECURITY_AUDIT_ENGINE=On
ENV MODSECURITY_AUDIT_LOG=/var/log/modsecurity/audit.log
ENV MODSECURITY_AUDIT_LOG_FORMAT=JSON
ENV VAULT_ADDR=http://127.0.0.1:8200
ENV PATH="${PATH}:/usr/local/bin"

# Crear punto de montaje
VOLUME ["/etc/vault.d/data"]

USER nginxuser

CMD ["sh", "-c", "/usr/local/bin/init-vault.sh & nginx -g 'daemon off;'"]