#!/bin/sh

# Generar certificados SSL si no existen
if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
    /usr/local/bin/generate-ssl.sh
fi

# Iniciar Vault en background
vault server -dev \
    -dev-root-token-id="${VAULT_ROOT_TOKEN}" \
    -dev-listen-address="0.0.0.0:8200" &

sleep 5

# Configurar políticas
vault policy write django - <<EOF
path "secret/data/django/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Almacenar secretos por categorías
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

# Verificar y arrancar nginx
nginx -t || exit 1
exec nginx -g 'daemon off;'

# #!/bin/sh

# # Generar certificados SSL si no existen
# if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
#     /usr/local/bin/generate-ssl.sh
# fi

# # Iniciar Vault en background
# vault server -dev \
#     -dev-root-token-id="${VAULT_ROOT_TOKEN}" \
#     -dev-listen-address="0.0.0.0:8200" &

# # Esperar a que Vault esté listo
# sleep 5

# # Configurar política y secretos
# vault policy write django - <<EOF
# path "secret/data/django/*" {
#   capabilities = ["create", "read", "update", "delete", "list"]
# }
# EOF

# # Almacenar secretos de Django
# vault kv put secret/django/config \
#     SECRET_KEY="${DJANGO_SECRET_KEY}" \
#     DB_PASSWORD="${POSTGRES_PASSWORD}"

# # Verificar configuración de nginx
# nginx -t || exit 1

# # Iniciar nginx
# exec nginx -g 'daemon off;'