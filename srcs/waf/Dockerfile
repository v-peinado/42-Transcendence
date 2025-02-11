# instancia de modsecurity-crs con nginx y vault
FROM owasp/modsecurity-crs:nginx

# Configuración de la imagen
USER root

ARG VAULT_VERSION=1.15.2

# Combinar instalación, configuración y limpieza en una sola capa
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
	rm -rf /var/lib/apt/lists/* && \
	# Crear directorios
	mkdir -p \
	/var/log/modsecurity \
	/var/log/vault \
	/etc/vault.d/data \
	/etc/nginx/modsecurity.d \
	/etc/nginx/modsecurity/rules \
	/etc/modsecurity/crs \
	/tmp/ssl && \
	# Crear usuario y configurar permisos en una sola capa
	useradd -r -s /sbin/nologin nginxuser || true && \
	chown -R nginxuser:nginxuser \
	/var/log/modsecurity \
	/var/log/vault \
	/etc/vault.d \
	/tmp/ssl \
	/tmp/modsecurity \
	/etc/nginx/modsecurity.d \
	/etc/nginx/modsecurity && \
	chmod 755 /etc/vault.d && \
	chmod 750 /etc/vault.d/data && \
	chmod -R 755 /var/log/vault && \
	touch /var/log/vault/audit.log && \
	chmod 640 /var/log/vault/audit.log && \
	chown -R nginxuser:nginxuser /var/log/vault/audit.log

# Copiar archivos de configuración (mantener COPY separado ya que cambia más frecuentemente)
COPY waf/vault/config.conf /etc/vault.d/config.hcl
COPY waf/vault/init-vault.sh /usr/local/bin/
COPY waf/custom-nginx.conf /etc/nginx/nginx.conf
COPY ssl/generate-ssl.sh /usr/local/bin/
COPY ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh
COPY waf/modsecurity/modsecurity.conf /etc/nginx/modsecurity.d/
COPY waf/modsecurity/rules/ /etc/nginx/modsecurity/rules/
COPY waf/modsecurity/crs-setup.conf /etc/modsecurity/crs/crs-setup.conf

# Configurar permisos de archivos copiados y generar SSL en una sola capa
RUN chmod +x \
	/usr/local/bin/generate-ssl.sh \
	/usr/local/bin/init-vault.sh \
	/docker-entrypoint.d/20-generate-ssl.sh && \
	ln -sf /etc/nginx/modsecurity/rules/main.conf /etc/nginx/modsecurity.d/main.conf && \
	chmod 644 /etc/nginx/modsecurity.d/* \
	/etc/nginx/modsecurity/rules/* \
	/etc/modsecurity/crs/* && \
	/usr/local/bin/generate-ssl.sh

# Variables de entorno
ENV MODSECURITY=On \
	VAULT_ADDR=https://127.0.0.1:8200 \
	VAULT_SKIP_VERIFY=true \
	PATH="${PATH}:/usr/local/bin"

# Puertos de la aplicación
EXPOSE 8081 8200 8445

# HEALTHCHECK para el contenedor
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
	CMD curl -f -k https://localhost:8444/health || exit 1

# Comando de inicio
CMD ["sh", "-c", "/usr/local/bin/init-vault.sh && nginx -g 'daemon off;'"]