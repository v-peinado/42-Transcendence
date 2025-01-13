# Configuración de almacenamiento
storage "file" {
  path = "/etc/vault.d/data"
}

# Configuración del servidor
listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"

ui = true
disable_mlock = true

telemetry {
  disable_hostname = true
}

default_lease_ttl = "24h"
max_lease_ttl = "48h"
cluster_name = "transcendence-vault"