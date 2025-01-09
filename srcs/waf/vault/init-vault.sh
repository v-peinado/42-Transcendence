#!/bin/sh

# Variables de configuración
VAULT_MODE=${VAULT_MODE:-"production"}  # Valores: "development" o "production"
LOG_DIR="/var/log/vault"
AUDIT_LOG="${LOG_DIR}/audit.log"
ERROR_LOG="${LOG_DIR}/error.log"
SYSTEM_LOG="${LOG_DIR}/system.log"
OPERATION_LOG="${LOG_DIR}/operation.log"
VAULT_CONFIG="/etc/vault.d/config.hcl"

# Función para logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${OPERATION_LOG}"
}

# Configuración inicial
setup_initial() {
    mkdir -p "${LOG_DIR}"
    chmod 755 "${LOG_DIR}"
    touch "${OPERATION_LOG}"
    chmod 640 "${OPERATION_LOG}"

    if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
        log_message "Generando certificados SSL..."
        /usr/local/bin/generate-ssl.sh 2>> "${ERROR_LOG}"
    fi
}

# Iniciar Vault según modo
start_vault() {
    if [ "${VAULT_MODE}" = "development" ]; then
        log_message "Iniciando Vault en modo desarrollo..."
        vault server -dev \
            -dev-root-token-id="${VAULT_ROOT_TOKEN}" \
            -dev-listen-address="0.0.0.0:8200" \
            -log-level=info \
            2>> "${ERROR_LOG}" \
            1>> "${SYSTEM_LOG}" &
    else
        log_message "Iniciando Vault en modo producción..."
        vault server -config="${VAULT_CONFIG}" \
            2>> "${ERROR_LOG}" \
            1>> "${SYSTEM_LOG}" &
    fi
    sleep 5
}

# Inicializar Vault en producción
initialize_vault() {
    if [ "${VAULT_MODE}" = "production" ]; then
        if ! vault status > /dev/null 2>&1; then
            log_message "Inicializando Vault..."
            vault operator init -key-shares=5 -key-threshold=3 > "${LOG_DIR}/init.txt"
        fi

        if vault status 2>/dev/null | grep -q "Sealed: true"; then
            log_message "Unsealing Vault..."
            cat "${LOG_DIR}/init.txt" | grep "Unseal Key" | awk '{print $4}' | head -n 3 | \
            while read key; do
                vault operator unseal "$key"
            done
        fi

        ROOT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
        vault login "$ROOT_TOKEN"
    fi
}

# Configurar Vault
configure_vault() {
    export VAULT_ADDR='https://127.0.0.1:8200'
    export VAULT_TOKEN="${VAULT_ROOT_TOKEN}"
    export VAULT_SKIP_VERIFY=true

    log_message "Configurando auditoría..."
    vault audit enable file \
        file_path="${AUDIT_LOG}" \
        mode="0640" \
        log_raw=true \
        format=json \
        prefix="vault-audit" \
        description="Audit logs for Vault operations"

    log_message "Configurando políticas de acceso..."
    vault policy write django - <<EOF
path "secret/data/django/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF
}

# Almacenar secretos
store_secrets() {
    log_message "Almacenando secretos de Django..."
    vault kv put secret/django/database \
        ENGINE="${SQL_ENGINE}" \
        NAME="${POSTGRES_DB}" \
        USER="${POSTGRES_USER}" \
        PASSWORD="${POSTGRES_PASSWORD}" \
        HOST="${SQL_HOST}" \
        PORT="${SQL_PORT}"

    vault kv put secret/django/oauth \
        CLIENT_ID="${FORTYTWO_CLIENT_ID}" \
        CLIENT_SECRET="${FORTYTWO_CLIENT_SECRET}" \
        REDIRECT_URI="${FORTYTWO_REDIRECT_URI}" \
        API_UID="${FORTYTWO_API_UID}" \
        API_SECRET="${FORTYTWO_API_SECRET}"

    vault kv put secret/django/email \
        HOST="${EMAIL_HOST}" \
        PORT="${EMAIL_PORT}" \
        USE_TLS="${EMAIL_USE_TLS}" \
        HOST_USER="${EMAIL_HOST_USER}" \
        HOST_PASSWORD="${EMAIL_HOST_PASSWORD}" \
        FROM_EMAIL="${DEFAULT_FROM_EMAIL}"

    vault kv put secret/django/security \
        SECRET_KEY="${DJANGO_SECRET_KEY}" \
        JWT_SECRET="${JWT_SECRET_KEY}"
}

# Iniciar nginx
start_nginx() {
    log_message "Verificando configuración de nginx..."
    nginx -t || {
        log_message "Error en configuración de nginx"
        exit 1
    }

    log_message "Iniciando nginx..."
    exec nginx -g 'daemon off;'
}

# Ejecución principal
setup_initial
start_vault
initialize_vault
configure_vault
store_secrets
start_nginx
