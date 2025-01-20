#!/bin/sh

set -e  				# Salir en caso de error
trap 'cleanup' EXIT		# Limpiar al salir

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Variables de configuración
SSL_DIR="/tmp/ssl"
KEY_FILE="${SSL_DIR}/transcendence.key"
CERT_FILE="${SSL_DIR}/transcendence.crt"
CONF_FILE="${SSL_DIR}/openssl.cnf"


# Función de limpieza al salir del script
cleanup() {
    if [ $? -ne 0 ]; then
        rm -f "$KEY_FILE" "$CERT_FILE" "$CONF_FILE"
        log_error "Script terminado con errores"
    fi
}

# Mensajes de log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Mensajes de error
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Crear directorio para almacenar certificados SSL y configuración de certificado
create_ssl_directory() {
    log_info "Creando directorios..."
    install -d -m 755 "$SSL_DIR" || {
        log_error "No se pudo crear $SSL_DIR"
        return 1
    }

    # Crear configuración de certificado
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

# Generar certificados SSL autofirmados
generate_certificates() {
    log_info "Generando certificados SSL..."
    
    # Limpiar certificados anteriores si existen
    rm -f "$CERT_FILE" "$KEY_FILE"
    
    # Generar certificados SSL autofirmados
    openssl req -x509 -nodes \
        -days 365 \
        -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -config "$CONF_FILE" \
        -extensions v3_req \
        -copy_extensions=copy || return 1
    
    # Establecer permisos adecuados
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    # Comprobar que los certificados se han generado correctamente
    [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ] || {
        log_error "Verificación de certificados fallida"
        return 1
    }
    
    log_info "Certificados generados en: $SSL_DIR"
}

# Función principal 
main() {
    log_info "Iniciando configuración SSL..."
    create_ssl_directory && generate_certificates
    log_info "Configuración SSL completada"
}

main