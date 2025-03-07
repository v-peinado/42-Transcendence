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

COPY nginx/conf/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf/default.conf /etc/nginx/templates/default.conf.template
# Agregar archivo de configuración dedicada para health check
COPY nginx/conf/health.conf /etc/nginx/conf.d/000-health.conf

# Script para corregir el health check
COPY nginx/health_fix.sh /usr/local/bin/health_fix.sh
RUN chmod +x /usr/local/bin/health_fix.sh

EXPOSE 8443

# Modificar el comando para ejecutar el script de corrección
CMD ["/bin/bash", "-c", "/usr/local/bin/health_fix.sh && nginx -g 'daemon off;'"]
