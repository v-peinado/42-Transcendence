#!/bin/sh

# Iniciar Vault en modo desarrollo
vault server -dev -dev-root-token-id=myroot -dev-listen-address=0.0.0.0:8200 &

# Esperar a que Vault esté listo
sleep 5

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN=myroot

# Habilitar secrets engine
vault secrets enable -path=secret kv-v2

# Crear política para Django
vault policy write django - <<EOF
path "secret/data/django/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Almacenar secretos iniciales
vault kv put secret/django/config \
    SECRET_KEY="tu_django_secret_key" \
    DB_PASSWORD="tu_db_password"

# Habilitar auditoría
vault audit enable file file_path=/var/log/vault/audit.log

# Mantener nginx en segundo plano
nginx -g 'daemon off;'

# #!/bin/sh

# # Inicializar Vault
# vault operator init > /etc/vault.d/init.txt

# # Desbloquear Vault
# vault operator unseal $(grep 'Key 1:' /etc/vault.d/init.txt | awk '{print $NF}')
# vault operator unseal $(grep 'Key 2:' /etc/vault.d/init.txt | awk '{print $NF}')
# vault operator unseal $(grep 'Key 3:' /etc/vault.d/init.txt | awk '{print $NF}')

# # Login
# vault login $(grep 'Initial Root Token:' /etc/vault.d/init.txt | awk '{print $NF}')

# # Habilitar secrets engine
# vault secrets enable -path=secret kv-v2

# # Crear política para Django
# vault policy write django - <<EOF
# path "secret/data/django/*" {
#   capabilities = ["create", "read", "update", "delete", "list"]
# }
# EOF

# # Almacenar secretos iniciales
# vault kv put secret/django/config \
#     SECRET_KEY="tu_django_secret_key" \
#     DB_PASSWORD="tu_db_password" \
#     OAUTH_CLIENT_ID="tu_oauth_id" \
#     OAUTH_CLIENT_SECRET="tu_oauth_secret"

# # Habilitar auditoría
# vault audit enable file file_path=/var/log/vault/audit.log

# # Verificar estado
# vault status

# # Mantener el proceso en ejecución
# exec nginx -g 'daemon off;'