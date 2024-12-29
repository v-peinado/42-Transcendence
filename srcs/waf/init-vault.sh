#!/bin/sh

# Generar certificados SSL si no existen
if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
    /usr/local/bin/generate-ssl.sh
fi

# Configurar Vault
export VAULT_ADDR='http://0.0.0.0:8200'
export VAULT_TOKEN="${VAULT_ROOT_TOKEN}"

# Iniciar Vault en background
vault server -dev \
    -dev-root-token-id="${VAULT_ROOT_TOKEN}" \
    -dev-listen-address="0.0.0.0:8200" &

# Esperar a que Vault esté listo
sleep 5

# Configurar política y secretos
vault policy write django - <<EOF
path "secret/data/django/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Almacenar secretos
vault kv put secret/django/config \
    SECRET_KEY="${DJANGO_SECRET_KEY}" \
    DB_PASSWORD="${POSTGRES_PASSWORD}"

# Verificar configuración de nginx
nginx -t || exit 1

# Iniciar nginx
exec nginx -g 'daemon off;'