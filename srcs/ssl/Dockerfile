FROM alpine:latest

RUN apk update && \
	apk add --no-cache openssl bash

COPY generate-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-ssl.sh

VOLUME /ssl

CMD ["/usr/local/bin/generate-ssl.sh"]
