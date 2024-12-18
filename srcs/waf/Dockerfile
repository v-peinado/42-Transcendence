FROM owasp/modsecurity-crs:nginx

USER root

WORKDIR /app

# Instalar HashiCorp Vault y dependencias
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -fsSL https://releases.hashicorp.com/vault/1.13.0/vault_1.13.0_linux_amd64.zip -o vault.zip && \
    unzip vault.zip && \
    mv vault /usr/local/bin/ && \
    rm vault.zip

# Crear directorios y configurar permisos
RUN mkdir -p /var/log/modsecurity \
            /etc/vault.d/data \
            /etc/modsecurity/rules \
            /var/log/vault \
            /var/run/nginx && \
    useradd -r -s /sbin/nologin nginxuser || true && \
    chown -R nginxuser:nginxuser \
        /var/log/modsecurity \
        /etc/vault.d \
        /etc/modsecurity/rules \
        /var/log/vault \
        /var/run/nginx

# Copiar archivos de configuración
COPY ./rules/ /etc/modsecurity/rules/
COPY ./vault/config.hcl /etc/vault.d/
COPY ./init-vault.sh /usr/local/bin/

# Copiar script de generación de SSL
COPY ./ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh

# Establecer permisos de ejecución
RUN chmod +x /usr/local/bin/init-vault.sh

# Variables de entorno
ENV MODSECURITY=On
ENV MODSECURITY_AUDIT_ENGINE=On
ENV MODSECURITY_AUDIT_LOG=/var/log/modsecurity/audit.log
ENV MODSECURITY_AUDIT_LOG_FORMAT=JSON
ENV VAULT_ADDR=http://127.0.0.1:8200
ENV PATH="${PATH}:/usr/local/bin"

# Crear punto de montaje
VOLUME ["/etc/vault.d/data", "/var/log/modsecurity"]

# Verificar la configuración de nginx
RUN nginx -t

# Mantener root como usuario para el inicio
USER root

# Exponer puertos necesarios
EXPOSE 443 8200

# Comando de inicio modificado para ejecutar como root
CMD ["/usr/local/bin/init-vault.sh"]