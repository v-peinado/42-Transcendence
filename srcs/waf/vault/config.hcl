storage "file" {
  path = "/etc/vault.d/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

ui = true
api_addr = "http://0.0.0.0:8200"
disable_mlock = true

# Configuración de auditoría
audit {
  type = "file"
  options = {
    file_path = "/var/log/vault/audit.log"
  }
}

# Política por defecto
default_lease_ttl = "24h"
max_lease_ttl = "48h"

# Configuración de plugins
plugin_directory = "/etc/vault.d/plugins"

# Configuración de cluster
cluster_addr = "http://0.0.0.0:8201"
cluster_name = "transcendence-vault"