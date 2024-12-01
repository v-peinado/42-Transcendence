#!/bin/bash

# Definición de colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Array para almacenar los tests fallidos
failed_tests=()

# Función para colorear la salida de los tests y registrar fallos
colorize_output() {
    while IFS= read -r line; do
        if [[ $line == *"ok"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"FAIL"* ]] || [[ $line == *"ERROR"* ]]; then
            echo -e "${RED}$line${NC}"
            # Extraer y almacenar el nombre del test fallido
            if [[ $line =~ ^(FAIL|ERROR):\ (.+)$ ]]; then
                failed_tests+=("${BASH_REMATCH[2]}")
            fi
        else
            echo "$line"
        fi
    done
}

# Función para verificar si un servicio está activo
check_service() {
    if docker ps --format '{{.Names}}' | grep -q "$1"; then
        return 0
    else
        return 1
    fi
}

# Función para esperar a que un servicio esté listo
wait_for_service() {
    printf "${BLUE}Esperando a que el servicio $1 esté listo...${NC}\n"
    local max_attempts=30
    local attempt=1
    
    while ! check_service "$1"; do
        if [ $attempt -gt $max_attempts ]; then
            printf "${RED}El servicio $1 no pudo iniciarse${NC}\n"
            return 1
        fi
        printf "."
        sleep 2
        attempt=$((attempt + 1))
    done
    printf "\n${GREEN}Servicio $1 listo${NC}\n"
    return 0
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    printf "${RED}Error: Este script debe ejecutarse desde el directorio raíz${NC}\n"
    exit 1
fi

# Iniciar servicios si no están activos
if ! check_service "web"; then
    printf "${BLUE}Iniciando servicios...${NC}\n"
    docker-compose up -d
    wait_for_service "web"
fi

# Ejecutar todos los tests
echo -e "\n${BLUE}=== Iniciando pruebas de autenticación ===${NC}\n"

if docker-compose exec web python manage.py test authentication --verbosity=2 | colorize_output; then
    printf "${GREEN}✓ Todos los tests completados exitosamente${NC}\n"
else
    printf "${RED}✗ Error en los tests${NC}\n"
    echo -e "\n${RED}Tests fallidos:${NC}"
    for test in "${failed_tests[@]}"; do
        echo -e "${RED}• $test${NC}"
    done
    exit 1
fi