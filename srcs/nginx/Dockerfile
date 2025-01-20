FROM nginx:alpine

USER root

RUN apk add --no-cache openssl && \
    mkdir -p \
        /tmp/ssl \
        /etc/nginx/ssl && \
    chown -R nginx:nginx \
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

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/templates /etc/nginx/templates
COPY nginx/frontend /usr/share/nginx/html
COPY ssl/generate-ssl.sh /docker-entrypoint.d/20-generate-ssl.sh

RUN chmod +x /docker-entrypoint.d/20-generate-ssl.sh

EXPOSE 8080 8443

CMD ["nginx", "-g", "daemon off;"]