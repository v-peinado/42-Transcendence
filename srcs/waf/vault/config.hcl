# Configuración de almacenamiento
	# Donde se guardarán los datos encriptados
storage "file" {
  path = "/etc/vault.d/data"
}

# Configuración del servidor
	# Donde Vault escucha las peticiones
listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 0
  tls_cert_file = "/tmp/ssl/transcendence.crt"
  tls_key_file  = "/tmp/ssl/transcendence.key"
  tls_min_version = "tls12"
}

api_addr = "https://0.0.0.0:8200"
cluster_addr = "https://0.0.0.0:8201"

ui = true
disable_mlock = true

telemetry {
  disable_hostname = true
}

#TLS (Transport Layer Security) es un protocolo de seguridad
#Proporciona comunicación cifrada entre cliente y servidor
#Evita interceptación de datos sensibles


# Configuración de auditoría con permisos correctos
	# Registro de todas las operaciones para seguridad
audit_device "file" {
  path = "/var/log/vault/audit.log"
  mode = "0640"
}

# Duración de los tokens de acceso
	# - default_lease_ttl: Tiempo de vida por defecto (24 horas)
default_lease_ttl = "24h"

	# - max_lease_ttl: Tiempo máximo permitido (48 horas)
max_lease_ttl = "48h"

# Nombre del cluster
	# Identificador único para servidor Vault
cluster_name = "transcendence-vault"