#!/bin/sh

# Variables
SSL_DIR="/tmp/ssl"
KEY_FILE="${SSL_DIR}/transcendence.key"
CERT_FILE="${SSL_DIR}/transcendence.crt"
CERT_SUBJECT="/C=ES/ST=Madrid/L=Madrid/O=42/OU=42Madrid/CN=localhost"

# Crear directorio
mkdir -p "$SSL_DIR"

# Generar certificados
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "$CERT_SUBJECT"

# Establecer permisos
chmod 644 "$CERT_FILE" "$KEY_FILE"
chown -R nginxuser:nginxuser "$SSL_DIR"
