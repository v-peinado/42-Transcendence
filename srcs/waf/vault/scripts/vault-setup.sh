#!/bin/bash

# Este es el script principal que orquesta todo el proceso de configuración.
# Responsabilidades:
# - Carga de módulos necesarios
# - Coordinación de la secuencia de inicialización
# - Validación de dependencias
# - Manejo de errores global
# - Limpieza de variables sensibles
# - Inicio del servidor nginx
#
# El script asegura que cada paso se complete correctamente
# antes de continuar con el siguiente, proporcionando
# una inicialización robusta y segura del sistema.

# Cargar los módulos necesarios
for module in logger.sh vault-config.sh vault-init.sh vault-secrets.sh; do
    if [ -f "/usr/local/bin/${module}" ]; then
        source "/usr/local/bin/${module}"
    else
        echo "Error: No se encuentra el módulo ${module}"
        exit 1
    fi
done

# Inicializar servicios en orden
setup_initial || exit 1
start_vault || exit 1
initialize_vault || exit 1
configure_vault || exit 1
store_secrets || exit 1

# Limpiar variables sensibles
unset VAULT_TOKEN
trap 'unset VAULT_TOKEN' EXIT

# Iniciar nginx
exec nginx -g 'daemon off;'
