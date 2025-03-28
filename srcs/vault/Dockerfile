FROM alpine:3.16

ARG VAULT_VERSION=1.15.2

# Combine installation and configuration in a single layer
RUN apk add --no-cache \
	curl \
	unzip \
	openssl \
	jq \
	bash \
	gettext \
	ncurses \
	&& curl -fsSL https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip -o vault.zip \
	&& unzip vault.zip \
	&& mv vault /usr/local/bin/ \
	&& rm vault.zip \
	&& mkdir -p \
	/var/log/vault \
	/etc/vault.d/data \
	/tmp/ssl \
	&& chmod 777 /var/log/vault \
	&& chmod 777 /etc/vault.d \
	&& chmod 777 /etc/vault.d/data \
	&& chmod 777 /tmp/ssl \
	&& touch /var/log/vault/audit.log \
	&& chmod 666 /var/log/vault/audit.log

# Ensure the directories exist and have proper permissions
RUN mkdir -p /var/log/vault \
	/etc/vault.d/data \
	/tmp/ssl && \
	chmod -R 777 /var/log/vault \
	/etc/vault.d \
	/etc/vault.d/data \
	/tmp/ssl && \
	touch /var/log/vault/audit.log && \
	chmod 666 /var/log/vault/audit.log

# Copy configuration files for vault
COPY srcs/vault/config.conf /etc/vault.d/config.hcl
COPY srcs/vault/scripts/ /usr/local/bin/
COPY srcs/ssl/generate-ssl.sh /usr/local/bin/

# Define log directory variables
ENV LOG_DIR=/var/log/vault \
	OPERATION_LOG=/var/log/vault/operation.log \
	ERROR_LOG=/var/log/vault/error.log

# Set proper permissions
RUN chmod +x \
	/usr/local/bin/vault-setup.sh \
	/usr/local/bin/vault-config.sh \
	/usr/local/bin/vault-init.sh \
	/usr/local/bin/vault-secrets.sh \
	/usr/local/bin/logger.sh \
	/usr/local/bin/generate-ssl.sh

# Environment variables
ENV VAULT_ADDR='https://127.0.0.1:8200' \
	# disable TLS verification (self-signed certificates)
	VAULT_SKIP_VERIFY=true \
	PATH="${PATH}:/usr/local/bin"

# Application port
EXPOSE 8200

# Set healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
	CMD vault status -tls-skip-verify && test -f /tmp/ssl/django_token || exit 1

# Set the startup command with permissions check
CMD ["sh", "-c", "chmod -R 777 /tmp/ssl || true && /usr/local/bin/vault-setup.sh"]
