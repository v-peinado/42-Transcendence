storage "file" {
  path = "/etc/vault.d/data"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1
}

# Configuración de auditoría
audit_device "file" {
  path = "/var/log/vault/audit.log"
}

# Configuración básica
default_lease_ttl = "24h"
max_lease_ttl = "48h"

cluster_name = "transcendence-vault"