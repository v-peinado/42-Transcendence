FROM alpine:latest

RUN apk add --no-cache openssl bash curl jq

WORKDIR /ssl

COPY ssl/generate-ssl.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-ssl.sh

CMD ["generate-ssl.sh"]
