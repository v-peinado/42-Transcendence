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
CERT_SUBJECT="/C=ES/ST=Madrid/L=Madrid/O=42/OU=42Madrid/CN=localhost"

# Función de limpieza
cleanup() {
    if [ $? -ne 0 ]; then
        rm -f "$KEY_FILE" "$CERT_FILE"
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
}

generate_certificates() {
    log_info "Generando certificados SSL..."
    
    # Limpiar certificados anteriores
    rm -f "$CERT_FILE" "$KEY_FILE"
    
    # Generar certificados
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "$CERT_SUBJECT" -sha256 || return 1
    
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

# #!/bin/sh

# # Variables de configuración almacenadas en el directorio /tmp/ssl

# SSL_DIR="/tmp/ssl"

# KEY_FILE="${SSL_DIR}/transcendence.key"
# CERT_FILE="${SSL_DIR}/transcendence.crt"
# CERT_SUBJECT="/C=ES/ST=Madrid/L=Madrid/O=42/OU=42Madrid/CN=localhost"

# # Para mostrar mensajes de log con colores y formato en la terminal 
# log_info() {
#     echo -e "[INFO] $1"
# }

# log_error() {
#     echo -e "[ERROR] $1"
# }

# # Función para crear directorios
# create_ssl_directory() {
#     log_info "Creando directorios..."
#     mkdir -p "$SSL_DIR" || {
#         log_error "No se pudo crear $SSL_DIR"
#         exit 1
#     }
#     # Asegurar permisos
#     chmod 755 "$SSL_DIR"
# }

# # Generar certificados
# generate_certificates() {
#     log_info "Verificando certificados..."
    
#     # Forzar regeneración de certificados
#     rm -f "$CERT_FILE" "$KEY_FILE"
    
#     log_info "Generando nuevos certificados SSL..."
#     openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#         -keyout "$KEY_FILE" \
#         -out "$CERT_FILE" \
#         -subj "$CERT_SUBJECT" || {
#             log_error "Error generando certificados"
#             exit 1
#         }
    
#     # Establecer permisos correctos
#     chmod 644 "$CERT_FILE" || {
#         log_error "Error estableciendo permisos del certificado"
#         exit 1
#     }
#     chmod 600 "$KEY_FILE" || {
#         log_error "Error estableciendo permisos de la key"
#         exit 1
#     }
    
#     # Verificar que los archivos existen
#     if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
#         log_error "Los certificados no se generaron correctamente"
#         exit 1
#     fi
    
#     log_info "Certificados generados en: $SSL_DIR"
# }

# # Función principal
# main() {
#     log_info "Iniciando configuración SSL..."
#     create_ssl_directory
#     generate_certificates
#     log_info "Configuración SSL completada"
# }

# # Ejecutar script
# main