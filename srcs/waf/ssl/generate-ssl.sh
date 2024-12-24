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

# #!/bin/sh

# # Variables de configuración
# SSL_DIR="/etc/nginx/ssl"
# KEY_FILE="${SSL_DIR}/transcendence.key"
# CERT_FILE="${SSL_DIR}/transcendence.crt"
# CERT_SUBJECT="/C=ES/ST=Madrid/L=Madrid/O=42/OU=42Madrid/CN=localhost"

# # Funciones de log
# log_info() {
#     echo -e "[INFO] $1"
# }

# log_error() {
#     echo -e "[ERROR] $1"
# }

# # Crear directorio SSL
# create_ssl_directory() {
#     log_info "Creando directorios..."
#     mkdir -p "$SSL_DIR" || {
#         log_error "No se pudo crear $SSL_DIR"
#         exit 1
#     }
# }

# # Generar certificados
# generate_certificates() {
#     # Solo generar si no existen
#     if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
#         log_info "Generando certificados SSL..."
#         openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#             -keyout "$KEY_FILE" \
#             -out "$CERT_FILE" \
#             -subj "$CERT_SUBJECT" || {
#                 log_error "Error generando certificados"
#                 exit 1
#             }
        
#         # Establecer permisos
#         chmod 644 "$CERT_FILE" || {
#             log_error "Error estableciendo permisos del certificado"
#             exit 1
#         }
#         chmod 600 "$KEY_FILE" || {
#             log_error "Error estableciendo permisos de la key"
#             exit 1
#         }
#     else
#         log_info "Certificados existentes encontrados"
#     fi
# }

# # Función principal
# main() {
#     log_info "Iniciando configuración SSL..."
#     create_ssl_directory
#     generate_certificates
#     log_info "Configuración SSL completada"
# }

# main