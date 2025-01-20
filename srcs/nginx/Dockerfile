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

RUN rm -f /docker-entrypoint.d/10-generate-certificate.sh

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/templates /etc/nginx/templates
COPY nginx/frontend /usr/share/nginx/html
COPY ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh

RUN chmod +x /docker-entrypoint.d/20-generate-ssl.sh

EXPOSE 8443

CMD ["nginx", "-g", "daemon off;"]
