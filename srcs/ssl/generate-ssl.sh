#!/bin/bash

set -e # Exit on error
trap 'cleanup' EXIT # Cleanup when script exits (normal or error)

# Color definitions for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Directories
SSL_DIR="/ssl"
KEY_FILE="${SSL_DIR}/transcendence.key"
CERT_FILE="${SSL_DIR}/transcendence.crt"
CONF_FILE="${SSL_DIR}/openssl.cnf" # Configuration file for openssl

# Cleanup function to remove the configuration file if the script fails
cleanup() {
    if [ $? -ne 0 ]; then # If the script failed
        rm -f "$CONF_FILE"
        log_error "Script terminated with errors"
    fi
}

# Log informational messages
log_info() {
    printf "${GREEN}[INFO]${NC} %s\n" "$1"
}

# Log error messages
log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1" >&2
}

# Validate required environment variables
validate_env_vars() {
    local required_vars=( # List of required environment variables to parse
        "SSL_COUNTRY"
        "SSL_STATE"
        "SSL_LOCALITY"
        "SSL_ORGANIZATION"
        "SSL_ORGANIZATIONAL_UNIT"
        "SSL_COMMON_NAME"
        "SSL_DAYS"
        "SSL_KEY_SIZE"
    )

	# Check if the required environment variables are defined
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "The following environment variables are required but not defined:"
        for var in "${missing_vars[@]}"; do
            log_error "- $var"
        done
        return 1
    fi

    # Validate numeric values
    if ! [[ "$SSL_DAYS" =~ ^[0-9]+$ ]]; then
        log_error "SSL_DAYS must be a positive integer"
        return 1
    fi

    if ! [[ "$SSL_KEY_SIZE" =~ ^[0-9]+$ ]]; then
        log_error "SSL_KEY_SIZE must be a positive integer"
        return 1
    fi

    if [ "$SSL_KEY_SIZE" -lt 2048 ]; then
        log_error "SSL_KEY_SIZE must be at least 2048 bits for security"
        return 1
    fi

    return 0
}

create_ssl_config() {
    if ! validate_env_vars; then
        log_error "SSL Configuration failed: invalid environment variables"
        return 1
    fi

    cat > "$CONF_FILE" << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = ${SSL_COUNTRY}
ST = ${SSL_STATE}
L = ${SSL_LOCALITY}
O = ${SSL_ORGANIZATION}
OU = ${SSL_ORGANIZATIONAL_UNIT}
CN = ${SSL_COMMON_NAME}

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
    log_info "Generating SSL certificates..."
    
    # Clean up previous certificates if they exist
    rm -f "$CERT_FILE" "$KEY_FILE"
    
    # Generate certificate
    if ! openssl req -x509 \
        -nodes \
        -days "${SSL_DAYS}" \
        -newkey "rsa:${SSL_KEY_SIZE}" \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -config "$CONF_FILE" \
        -extensions v3_req 2>/tmp/openssl.err; then
        log_error "Error generating certificates:"
        cat /tmp/openssl.err >&2
        rm -f /tmp/openssl.err
        return 1
    fi
    rm -f /tmp/openssl.err

	# Define more permissive permissions so all containers can read these files (Auto sign the certificate)
    if ! chmod 666 "$CERT_FILE" 2>/dev/null; then
        log_error "Error setting permissions for $CERT_FILE"
        return 1
    fi

	# Make the key readable by all containers 
    if ! chmod 666 "$KEY_FILE" 2>/dev/null; then
        log_error "Error setting permissions for $KEY_FILE"
        return 1
    fi
    
	# Enssure that group permissions allow reading
	# Only attempt if the ssl-cert group exists
    if getent group ssl-cert > /dev/null 2>&1; then
        chown root:ssl-cert "$CERT_FILE" "$KEY_FILE" 2>/dev/null || log_info "Could not set group ownership (not critical)"
    else
        log_info "Group ssl-cert not found, skipping group ownership settings"
    fi
    
    # Store in Vault if configured
    if [ -n "$VAULT_ADDR" ]; then
        if [ -z "$VAULT_ROOT_TOKEN" ]; then
            log_error "VAULT_ROOT_TOKEN is not defined"
            return 1
        fi
    
	# Encode the certificate and key as base64
        cert_data=$(base64 -w 0 "$CERT_FILE")
        key_data=$(base64 -w 0 "$KEY_FILE")
    
	# Store the certificate and key in Vault utilizing the token and address
        curl -k -H "X-Vault-Token: ${VAULT_ROOT_TOKEN}" \
             -X PUT \
             -d "{\"data\": {\"ssl_certificate\": \"${cert_data}\", \"ssl_certificate_key\": \"${key_data}\"}}" \
             "${VAULT_ADDR}/v1/secret/data/nginx/ssl"
    fi
    
    # Verify certificates
    if ! { [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; }; then
        log_error "Certificate verification failed"
        return 1
    fi

    # Verify certificate validity
    if ! openssl x509 -in "$CERT_FILE" -noout -text >/dev/null 2>&1; then
        log_error "Generated certificate is not valid"
        return 1
    fi
    
    log_info "Certificates generated successfully"
    return 0
}

main() {
    log_info "Starting SSL configuration..."
    
    if ! mkdir -p "$SSL_DIR" 2>/dev/null; then
        log_error "Could not create directory $SSL_DIR"
        exit 1
    fi

    if ! create_ssl_config; then
        exit 1
    fi

    if ! generate_certificates; then
        exit 1
    fi

    log_info "SSL configuration completed"
    log_info "NOTE: We are using self-signed certificates for development/academic purposes only"
}

main