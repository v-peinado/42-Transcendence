#!/bin/sh

# Generar certificados SSL si no existen
if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
    /usr/local/bin/generate-ssl.sh
fi

# Iniciar Vault en modo desarrollo
vault server -dev -dev-root-token-id=myroot -dev-listen-address=0.0.0.0:8200 &

# Esperar a que Vault esté listo
sleep 5

# Configurar Vault
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN=myroot

# Configurar política y secretos
vault policy write django - <<EOF
path "secret/data/django/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Almacenar secretos
vault kv put secret/django/config \
    SECRET_KEY="tu_django_secret_key" \
    DB_PASSWORD="tu_db_password"

# Verificar configuración de nginx
nginx -t || exit 1

# Iniciar nginx en primer plano
exec nginx -g 'daemon off;'