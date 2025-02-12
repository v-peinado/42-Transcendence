#!/bin/sh

set -e  					# Exit on error
trap 'cleanup' EXIT		# Clean up on exit

# Color definitions for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Configuration variables
SSL_DIR="/tmp/ssl"
KEY_FILE="${SSL_DIR}/transcendence.key"
CERT_FILE="${SSL_DIR}/transcendence.crt"
CONF_FILE="${SSL_DIR}/openssl.cnf"

# Cleanup function executed on script exit
cleanup() {
    if [ $? -ne 0 ]; then
        rm -f "$KEY_FILE" "$CERT_FILE" "$CONF_FILE"
        log_error "Script terminated with errors"
    fi
}

# Log informational messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Log error messages
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Create SSL directory and certificate configuration
create_ssl_directory() {
    log_info "Creating directories..."
    install -d -m 755 "$SSL_DIR" || {
        log_error "Could not create $SSL_DIR"
        return 1
    }

    # Create certificate configuration
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

# Generate self-signed SSL certificates
generate_certificates() {
    log_info "Generating SSL certificates..."
    
    # Clean up previous certificates if they exist
    rm -f "$CERT_FILE" "$KEY_FILE"
    
    # Generate self-signed SSL certificates
    openssl req -x509 -nodes \
        -days 365 \
        -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -config "$CONF_FILE" \
        -extensions v3_req \
        -copy_extensions=copy || return 1
    
    # Set appropriate permissions
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    # Verify certificates were generated successfully
    [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ] || {
        log_error "Certificate verification failed"
        return 1
    }
    
    log_info "Certificates generated in: $SSL_DIR"
}

# Main function - Script entry point
main() {
    log_info "Starting SSL configuration..."
    create_ssl_directory && generate_certificates
    log_info "SSL configuration completed"
}

main