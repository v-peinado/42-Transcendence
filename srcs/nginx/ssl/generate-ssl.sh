#!/bin/sh

# Variables de configuración
SSL_DIR="/etc/nginx/ssl"
TMP_SSL_DIR="/tmp/ssl"
KEY_FILE="${TMP_SSL_DIR}/transcendence.key"
CERT_FILE="${TMP_SSL_DIR}/transcendence.crt"
CERT_SUBJECT="/C=ES/ST=Madrid/L=Madrid/O=42/OU=42Madrid/CN=localhost"

# Función para mostrar mensajes
log_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Función para verificar requisitos
check_requirements() {
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL no está instalado"
        exit 1
    fi
}

# Función para crear directorios
create_ssl_directory() {
    log_info "Creando directorios..."
    mkdir -p "$TMP_SSL_DIR" || {
        log_error "No se pudo crear el directorio SSL"
        exit 1
    }
}

# Función para generar certificados
generate_certificates() {
    log_info "Generando certificados SSL..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "$CERT_SUBJECT" || {
            log_error "Error generando certificados"
            exit 1
        }
    
    # Establecer permisos
    chmod 600 "$KEY_FILE" || {
        log_error "No se pudo establecer permisos para la key"
        exit 1
    }
    chmod 644 "$CERT_FILE" || {
        log_error "No se pudo establecer permisos para el certificado"
        exit 1
    }
    
    log_info "Certificados generados correctamente"
}

# Función principal
main() {
    log_info "Iniciando configuración SSL..."
    check_requirements
    create_ssl_directory
    generate_certificates
    log_info "Configuración SSL completada con éxito"
}

# Ejecutar script
main