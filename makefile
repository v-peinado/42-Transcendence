# Nombre del archivo de composición de Docker por defecto
COMPOSE_FILE = ./srcs/docker-compose.yml

# Comando para Docker Compose (compatible con V2)
COMPOSE_CMD = docker compose

# Variables de colores para los mensajes
COLOR_GREEN = \033[0;32m
COLOR_RED = \033[0;31m
COLOR_RESET = \033[0m

# Cargar las variables del archivo .env
include srcs/.env
export $(shell cat srcs/.env | xargs)

# Detectar el sistema operativo y configurar las variables
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    export DOCKER_BIND_MOUNT=./django
    export DOCKER_HOME=$(HOME)
else
    export DOCKER_BIND_MOUNT=django_code
    export DOCKER_HOME=/goinfre/$(USER)
endif

all: up help

# Añadir una nueva regla para crear los directorios necesarios
create-media-dirs:
	@echo "$(COLOR_GREEN)Creando directorios para media...$(COLOR_RESET)"
	@mkdir -p srcs/django/media/profile_images
	@chmod 777 srcs/django/media/profile_images

# Comprobar y crear directorio goinfre en Linux
check-goinfre:
ifeq ($(UNAME_S),Linux)
	@echo "$(COLOR_GREEN)Comprobando directorio goinfre...$(COLOR_RESET)"
	@if [ ! -d "/goinfre" ]; then \
        echo "$(COLOR_RED)Directorio /goinfre no existe, creando...$(COLOR_RESET)"; \
        sudo mkdir -p /goinfre/$(USER); \
        sudo chown $(USER):$(USER) /goinfre/$(USER); \
    fi
	@if [ ! -d "/goinfre/$(USER)" ]; then \
        echo "$(COLOR_GREEN)Creando directorio de usuario en goinfre...$(COLOR_RESET)"; \
        mkdir -p /goinfre/$(USER); \
    fi
endif

# Levanta los servicios definidos en el archivo de composición
up: check-goinfre create-media-dirs configure-rootless
	@echo "$(COLOR_GREEN)Levantando servicios...$(COLOR_RESET)"
	@DOCKER_HOST=unix:///$(DOCKER_HOME)/.docker/run/docker.sock $(COMPOSE_CMD) -f $(COMPOSE_FILE) up -d

# Detiene y elimina los contenedores
down:
	@echo "$(COLOR_GREEN)Apagando servicios...$(COLOR_RESET)"
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) down

clean-postgres-data:
	@echo "$(COLOR_GREEN)Verificando si existe el volumen de datos de postgres para eliminar...$(COLOR_RESET)"
	@if docker volume inspect postgres_data > /dev/null 2>&1; then \
		echo "$(COLOR_GREEN)Eliminando volumen de datos de postgres...$(COLOR_RESET)"; \
		docker volume rm -f postgres_data; \
	else \
		echo "$(COLOR_GREEN)No hay volumen de datos de postgres para eliminar.$(COLOR_RESET)"; \
	fi

# Regla para limpiar volúmenes y medios
clean-volumes:
	@echo "$(COLOR_RED)Eliminando volúmenes y archivos media...$(COLOR_RESET)"
	@docker volume rm -f django_media 2>/dev/null || true
	@rm -rf srcs/django/media/profile_images/* 2>/dev/null || true  # Solo elimina el contenido, no el directorio

# Reinicia los servicios (down y luego up)
reset: down up
	@echo "$(COLOR_GREEN)Reinicio completado.$(COLOR_RESET)"

# Limpia contenedores y redes
clean: down
	@echo "$(COLOR_RED)Limpiando contenedores y redes...$(COLOR_RESET)"
	@docker container prune -f
	@docker network prune -f

# Limpieza completa incluyendo volúmenes
fclean: clean
	@echo "$(COLOR_RED)Limpiando todos los recursos, incluyendo volúmenes...$(COLOR_RESET)"
	@docker volume rm -f $$(docker volume ls -q | grep "srcs_")
	@docker system prune -af --volumes
	@rm -rf srcs/django/media/profile_images/*

# Apaga los servicios y ejecuta un prune
close: down
	@echo "$(COLOR_GREEN)Ejecutando prune tras apagar servicios...$(COLOR_RESET)"
	docker system prune -f

# Ejecuta docker compose up sin modo detach (para depuración)
debug:
	@echo "$(COLOR_GREEN)Ejecutando en modo de depuración...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) up

# Muestra el estado de los contenedores
status:
	@echo "$(COLOR_GREEN)Mostrando estado de los contenedores...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) ps

logs:
	@echo "$(COLOR_GREEN)Mostrando logs...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) logs -f

# Muestra un resumen de las imágenes de Docker
images:
	@echo "$(COLOR_GREEN)Mostrando imágenes de Docker...$(COLOR_RESET)"
	docker images

# Nombre de las imágenes
IMAGES = srcs-web postgres:17

# Regla para reconstruir todas las imágenes, para cambios en dockerfile
rebuild-images:
	@echo "$(COLOR_GREEN)Reconstruyendo todas las imágenes de Docker...$(COLOR_RESET)"
	@for image in $(IMAGES); do \
		echo "Reconstruyendo $$image..."; \
		docker build -t $$image . || exit 1; \
	done

# Regla para destruir (eliminar) todas las imágenes
destroy-images:
	@echo "$(COLOR_GREEN)Destruyendo todas las imágenes de Docker...$(COLOR_RESET)"
	@for image in $(IMAGES); do \
		if docker images $$image --format '{{.Repository}}' | grep -q "^$$image$$"; then \
			echo "Eliminando $$image..."; \
			docker rmi -f $$image || true; \
		else \
			echo "Imagen $$image no encontrada, omitiendo..."; \
		fi; \
	done
	# Eliminar todas las imágenes huérfanas
	@echo "$(COLOR_GREEN)Eliminando imágenes huérfanas...$(COLOR_RESET)"
	docker image prune -a -f

re: fclean all

# Regla principal para verificar la base de datos y las tablas
check_db_tables:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB) -c "\dt"

# Regla para conectarse a la base de datos (solo para verificar conexión)
connect_db:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB)

# Regla para listar las bases de datos
list_databases:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) -c "\l"

# Makefile para acceder a la base de datos PostgreSQL y ver los usuarios registrados

-include ./srcs/env

# Regla para ver todos los usuarios y sus campos
view-users:
	@echo "Conectando a la base de datos PostgreSQL y mostrando todos los campos de los usuarios..."
	@docker exec -it postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT * FROM authentication_customuser;"

# Configurar Docker rootless
configure-rootless:
ifeq ($(UNAME_S),Linux)
	@echo "$(COLOR_GREEN)Configurando Docker rootless...$(COLOR_RESET)"
	@mkdir -p $(DOCKER_HOME)/.docker
	@dockerd-rootless-setuptool.sh install
	@echo "export DOCKER_HOST=unix:///$(DOCKER_HOME)/.docker/run/docker.sock" >> ~/.bashrc
endif

# Ayuda para ver las reglas disponibles
help:
	@echo ""
	@echo "$(COLOR_GREEN)Reglas disponibles:$(COLOR_RESET)"
	@echo ""
	@echo "  make up                    - Levanta los servicios en modo detach"
	@echo "  make down                  - Detiene y elimina los servicios"
	@echo "  make reset                 - Reinicia los servicios (down + up)"
	@echo "  make clean                 - Limpia contenedores, imágenes y volúmenes no utilizados"
	@echo "  make close                 - Apaga servicios y ejecuta prune"
	@echo "  make debug                 - Levanta los servicios sin detach para depuración"
	@echo "  make fclean                - Cierra servicios y destruye todas las imágenes"
	@echo "  make re                    - Ejecuta fclean y luego up"
	@echo ""
	@echo "  make status                - Muestra el estado de los contenedores"
	@echo "  make logs                  - Muestra los logs de los contenedores"
	@echo "  make images                - Muestra un resumen de las imágenes de Docker"
	@echo ""
	@echo "  make rebuild-images        - Reconstruye todas las imágenes"
	@echo "  make destroy-images        - Destruye todas las imágenes"
	@echo "  make clean-postgres-data   - Elimina el volumen de datos de postgres"
	@echo ""
	@echo "  make view-users            - Muestra los usuarios autorizados en la base de datos"
	@echo ""
	@echo "  make help                  - Muestra esta ayuda"
	@echo ""
	@echo "  para ver la web desde django, accede a http://localhost:8000"
	@echo "  para ver la web desde nginx, accede a http://localhost:80"
	@echo ""
	
.PHONY: all up down logs reset clean close debug status images help rebuild-images destroy-images check_db_tables connect_db list_databases fclean re clean view-users view-tables view-users-fields

