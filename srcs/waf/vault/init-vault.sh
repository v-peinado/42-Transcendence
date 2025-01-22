#!/bin/sh

# Script de inicialización y configuración de HashiCorp Vault
# Propósito: Gestionar el almacenamiento seguro de secretos y políticas de acceso
# Pasos:
# - Inicialización y dessellado de Vault
# - Configuración de políticas y auditoría
# - Almacenamiento seguro de secretos de Django y Nginx
# - Integración con nginx para servir la aplicación

# Variables de configuración
VAULT_MODE=${VAULT_MODE:-"production"}  # Valores posibles: "development" o "production"
LOG_DIR="/var/log/vault"
AUDIT_LOG="${LOG_DIR}/audit.log"
ERROR_LOG="${LOG_DIR}/error.log"
SYSTEM_LOG="${LOG_DIR}/system.log"
OPERATION_LOG="${LOG_DIR}/operation.log"
VAULT_CONFIG="/etc/vault.d/config.hcl"

# Manejo de logs
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${OPERATION_LOG}"
}

# Configuración inicial
setup_initial() {

	# Crear directorios y archivos de log
    mkdir -p "${LOG_DIR}"
    chmod 755 "${LOG_DIR}"
    touch "${OPERATION_LOG}"
    chmod 640 "${OPERATION_LOG}"

	# Generar certificados SSL si no existen
    if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
        log_message "Generando certificados SSL..."
        /usr/local/bin/generate-ssl.sh 2>> "${ERROR_LOG}"
    fi
}

# Iniciar Vault en modo desarrollo o producción
start_vault() {

	# Modo desarrollo
    if [ "${VAULT_MODE}" = "development" ]; then
        log_message "Iniciando Vault en modo desarrollo..."
        vault server -dev \
            -dev-root-token-id="${VAULT_ROOT_TOKEN}" \
            -dev-listen-address="0.0.0.0:8200" \
            -log-level=debug &
    # Modo producción
	else
        log_message "Iniciando Vault en modo producción..."
        vault server -config="${VAULT_CONFIG}" \
            -log-level=debug &
    fi
    
    # Esperar a que Vault esté disponible antes de continuar con la configuración
    for i in $(seq 1 60); do
        if curl -s http://127.0.0.1:8200/v1/sys/health >/dev/null 2>&1; then
            log_message "Vault está disponible"
            return 0
        fi
        log_message "Esperando a que Vault inicie... intento $i"
        sleep 2
    done
    
    log_message "Error: Timeout esperando a Vault"
    return 1
}

# Una vez que Vault está disponible, seguir con la inicialización
initialize_vault() {
    if [ "${VAULT_MODE}" = "production" ]; then
        export VAULT_ADDR='http://127.0.0.1:8200'
        log_message "Configurando VAULT_ADDR=${VAULT_ADDR}"

        # Verificar si necesita inicialización
        if ! vault operator init -status > /dev/null 2>&1; then
            log_message "Inicializando Vault..."
            vault operator init -key-shares=1 -key-threshold=1 > "${LOG_DIR}/init.txt"
            chmod 600 "${LOG_DIR}/init.txt"
            chown nginxuser:nginxuser "${LOG_DIR}/init.txt"
            
            # Extraer las claves de dessellado y el token root para configurar Vault
            UNSEAL_KEY=$(grep "Unseal Key 1" "${LOG_DIR}/init.txt" | awk '{print $4}')
            ROOT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
            
            # Dessellar Vault
            log_message "Dessellando Vault..."
            vault operator unseal "$UNSEAL_KEY"
            
            # Configurar token root
            export VAULT_TOKEN="$ROOT_TOKEN"
            vault login "$ROOT_TOKEN"
        fi
    fi
}

configure_vault() {
    # Verificar que se ha encontrado el archivo de inicialización
    if [ ! -f "${LOG_DIR}/init.txt" ]; then
        log_message "Error: No se encuentra init.txt"
        return 1
    fi
    
    # Configurar variables de entorno para acceder a Vault
    export VAULT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
    export VAULT_ADDR='http://127.0.0.1:8200'
    
    # Verificar que Vault está dessellado
    until vault status >/dev/null 2>&1; do
        if vault status 2>/dev/null | grep -q "Sealed: true"; then
            UNSEAL_KEY=$(grep "Unseal Key 1" "${LOG_DIR}/init.txt" | awk '{print $4}')
            vault operator unseal "$UNSEAL_KEY"
        fi
        sleep 2
    done

    # Habilitar el motor KV si no está habilitado
    if ! vault secrets list | grep -q '^secret/'; then
        vault secrets enable -path=secret kv-v2
		log_message "Motor KV-2 habilitado"
    fi

	# Actualizar política para KV-v2
	log_message "Configurando políticas de acceso..."
	vault policy write django - <<-EOF
	# Permitir acceso a los secretos de Django
	path "secret/data/django/*" {
		capabilities = ["create", "read", "update", "delete", "list"]
	}

	# Permitir listar los secretos
	path "secret/metadata/django/*" {
		capabilities = ["list"]
	}

	# Permitir acceso a los secretos de Nginx
	path "secret/data/nginx/*" {
		capabilities = ["create", "read", "update", "delete", "list"]
	}

	path "secret/metadata/nginx/*" {
		capabilities = ["list"]
	}
	
	# Gestión de tokens
	path "auth/token/*-self" {
		capabilities = ["read", "update"]
}
	EOF
}

# Almacenar secretos en Vault
store_secrets() {
    # Verificar que tenemos acceso a Vault
    if ! vault token lookup >/dev/null 2>&1; then
        log_message "Error: No hay acceso válido a Vault"
        return 1
	fi

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

	vault kv put secret/django/settings \
    	DEBUG="${DJANGO_DEBUG}" \
    	ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS}" \
		SECRET_KEY="${DJANGO_SECRET_KEY}"
	
	vault kv put secret/django/jwt \
    	secret_key="${JWT_SECRET_KEY}" \
    	algorithm="${JWT_ALGORITHM}" \
    	expiration_time="${JWT_EXPIRATION_TIME}"

	vault kv put secret/nginx/ssl \
		ssl_certificate="$(base64 /tmp/ssl/transcendence.crt 2>/dev/null || echo '')" \
		ssl_certificate_key="$(base64 /tmp/ssl/transcendence.key 2>/dev/null || echo '')"
}

# Iniciar nginx para servir la aplicación
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
