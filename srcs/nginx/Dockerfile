FROM owasp/modsecurity-crs:nginx

USER root

ENV MODSECURITY=On \
	MODSECURITY_AUDIT_ENGINE=On \
	MODSECURITY_AUDIT_LOG=/var/log/modsecurity/audit.log \
	MODSECURITY_AUDIT_LOG_FORMAT=JSON

RUN apt-get update && \
	apt-get install -y openssl && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* && \
	mkdir -p \
	/var/log/modsecurity \
	/tmp/ssl \
	/etc/nginx/ssl \
	/etc/modsecurity/rules && \
	chown -R nginx:nginx \
	/var/log/modsecurity \
	/tmp/ssl \
	/etc/nginx \
	/var/cache/nginx \
	/var/log/nginx \
	/usr/share/nginx/html && \
	chmod -R 755 \
	/etc/nginx \
	/var/cache/nginx \
	/var/log/nginx \
	/usr/share/nginx/html

# Use certificates from shared volume /tmp/ssl/
RUN mv /docker-entrypoint.d/10-generate-certificate.sh /docker-entrypoint.d/10-generate-certificate.sh.original || true && \
	echo '#!/bin/sh' > /docker-entrypoint.d/10-generate-certificate.sh && \
	echo 'echo "Using certificates from shared volume /tmp/ssl/"' >> /docker-entrypoint.d/10-generate-certificate.sh && \
	echo 'exit 0' >> /docker-entrypoint.d/10-generate-certificate.sh && \
	chmod +x /docker-entrypoint.d/10-generate-certificate.sh

COPY nginx/conf/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf/default.conf /etc/nginx/templates/conf.d/default.conf.template

EXPOSE 8443

CMD ["nginx", "-g", "daemon off;"]
