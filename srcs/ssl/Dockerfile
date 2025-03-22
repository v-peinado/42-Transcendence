FROM alpine:latest

# Install required tools
RUN apk update && \
	apk add --no-cache openssl bash && \
	# Create ssl-cert group and add root user to it
	addgroup -S ssl-cert

COPY generate-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-ssl.sh

VOLUME /ssl

CMD ["/usr/local/bin/generate-ssl.sh"]
