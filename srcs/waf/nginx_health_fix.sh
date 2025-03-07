#!/bin/bash

# Script para verificar y corregir la configuración de health check en nginx
echo "Verificando configuración de Nginx..."

# Esperar a que nginx esté listo
sleep 5

# Verificar si nginx está ejecutándose
if ! pgrep -x "nginx" > /dev/null; then
    echo "Error: Nginx no está en ejecución"
    exit 1
fi

# Asegurar que la respuesta de health check sea directa
echo "
server {
    listen 8081;
    server_name localhost;

    location = /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 'OK';
    }
}
" > /etc/nginx/conf.d/health_check.conf

# Recargar nginx para aplicar cambios
echo "Recargando configuración de Nginx..."
nginx -s reload

echo "Corrección aplicada. Probando health check..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health)

if [ "$response" == "200" ]; then
    echo "Health check funcionando correctamente"
else
    echo "Error: Health check retorna $response en lugar de 200"
fi

exit 0
