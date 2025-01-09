#!/bin/sh

set -e  # Detener en errores
trap 'cleanup' EXIT  # Limpiar al salir

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Variables de configuración
SSL_DIR="/tmp/ssl"
KEY_FILE="${SSL_DIR}/transcendence.key"
CERT_FILE="${SSL_DIR}/transcendence.crt"
CONF_FILE="${SSL_DIR}/openssl.cnf"

# Función de limpieza
cleanup() {
    if [ $? -ne 0 ]; then
        rm -f "$KEY_FILE" "$CERT_FILE" "$CONF_FILE"
        log_error "Script terminado con errores"
    fi
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

create_ssl_directory() {
    log_info "Creando directorios..."
    install -d -m 755 "$SSL_DIR" || {
        log_error "No se pudo crear $SSL_DIR"
        return 1
    }

    # Crear archivo de configuración OpenSSL
    cat > "$CONF_FILE" << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = ES
ST = Madrid
L = Madrid
O = 42
OU = 42Madrid
CN = localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
EOF
}

generate_certificates() {
    log_info "Generando certificados SSL..."
    
    # Limpiar certificados anteriores
    rm -f "$CERT_FILE" "$KEY_FILE"
    
    # Generar certificados con extensiones
    openssl req -x509 -nodes \
        -days 365 \
        -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -config "$CONF_FILE" \
        -extensions v3_req \
        -copy_extensions=copy || return 1
    
    # Establecer permisos
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    # Verificación final
    [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ] || {
        log_error "Verificación de certificados fallida"
        return 1
    }
    
    log_info "Certificados generados en: $SSL_DIR"
}

main() {
    log_info "Iniciando configuración SSL..."
    create_ssl_directory && generate_certificates
    log_info "Configuración SSL completada"
}

main