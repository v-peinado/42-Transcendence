FROM alpine:latest

# Instalar herramientas necesarias y crear grupo ssl-cert
RUN apk update && \
	apk add --no-cache openssl bash && \
	# Crear el grupo ssl-cert para mantener consistencia con otros contenedores
	addgroup -S ssl-cert

COPY generate-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-ssl.sh

VOLUME /ssl

CMD ["/usr/local/bin/generate-ssl.sh"]
