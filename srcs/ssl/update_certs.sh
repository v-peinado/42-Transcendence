#!/bin/bash

# Script para regenerar certificados SSL con la dirección IP correcta
# Uso: ./update_certs.sh [IP_ADDRESS]

if [ -z "$1" ]; then
  echo "Uso: $0 [IP_ADDRESS]"
  echo "Ejemplo: $0 192.168.1.144"
  exit 1
fi

IP_ADDRESS=$1

# Actualizar .env con la nueva IP
sed -i '' "s/SSL_COMMON_NAME=.*/SSL_COMMON_NAME=$IP_ADDRESS/" ../srcs/.env
sed -i '' "s|FORTYTWO_REDIRECT_URI=.*|FORTYTWO_REDIRECT_URI=https://$IP_ADDRESS:8445/login/|" ../srcs/.env 
sed -i '' "s|FORTYTWO_API_URL=.*|FORTYTWO_API_URL=https://$IP_ADDRESS:8445/login/|" ../srcs/.env
sed -i '' "s|SITE_URL=.*|SITE_URL=https://$IP_ADDRESS:8445|" ../srcs/.env

echo "Archivo .env actualizado."
echo "Ahora ejecuta 'docker-compose down' y luego 'docker-compose up -d' para regenerar los certificados."
echo "Los otros clientes podrán acceder usando https://$IP_ADDRESS:8445"

# El contenedor ssl-manager regenerará los certificados al reiniciar
