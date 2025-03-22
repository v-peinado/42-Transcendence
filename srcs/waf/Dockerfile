# ModSecurity-CRS instance with nginx
FROM owasp/modsecurity-crs:nginx

# Image configuration
USER root

# Combine installation, configuration and cleanup in a single layer
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	curl \
	openssl \
	libmodsecurity3 \
	modsecurity-crs \
	jq \
	bash \
	ssl-cert \
	netcat-traditional \
	gettext-base && \ 
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* && \
	# Create directories and user
	mkdir -p \
	/var/log/modsecurity \
	/etc/nginx/modsecurity.d \
	/etc/nginx/modsecurity/rules \
	/etc/modsecurity/crs \
	/tmp/ssl && \
	# Create user and set permissions for directories
	useradd -r -s /sbin/nologin nginxuser || true && \
	chown -R nginxuser:nginxuser \
	/var/log/modsecurity \
	/tmp/ssl \
	/tmp/modsecurity \
	/etc/nginx/modsecurity.d \
	/etc/nginx/modsecurity

# Create group for SSL certificate access and add root to it 
RUN groupadd -r ssl-cert || true && \
	usermod -a -G ssl-cert root && \
	usermod -a -G ssl-cert nginxuser

# Copy configuration files - Updated paths for new structure
COPY srcs/ssl/generate-ssl.sh /usr/local/bin/
COPY srcs/ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh
COPY srcs/waf/modsecurity/modsecurity.conf /etc/nginx/modsecurity.d/
COPY srcs/waf/modsecurity/rules/ /etc/nginx/modsecurity/rules/
COPY srcs/waf/modsecurity/crs-setup.conf /etc/modsecurity/crs/crs-setup.conf
COPY srcs/waf/entrypoint.sh /usr/local/bin/

# Configure permissions with explicit chmod to ensure entrypoint is executable
RUN chmod 755 /usr/local/bin/generate-ssl.sh && \
	chmod 755 /docker-entrypoint.d/20-generate-ssl.sh && \
	chmod 755 /usr/local/bin/entrypoint.sh && \
	ln -sf /etc/nginx/modsecurity/rules/main.conf /etc/nginx/modsecurity.d/main.conf && \
	chmod 644 /etc/nginx/modsecurity.d/* \
	/etc/nginx/modsecurity/rules/* \
	/etc/modsecurity/crs/*

# Environment variables
ENV MODSECURITY=On \
	PATH="${PATH}:/usr/local/bin"

# Application ports
EXPOSE 8081 8444 8445

# Container HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
	CMD curl -f -k --max-time 1 http://localhost:8081/health || exit 1