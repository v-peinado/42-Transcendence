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

# Detectar sistema operativo
UNAME_S := $(shell uname -s)

# Configurar directorios según el sistema operativo
ifeq ($(UNAME_S),Linux)
    DOCKER_HOME=/goinfre/$(USER)
    DOCKER_SOCKET=$(DOCKER_HOME)/.docker/run/docker.sock
else
    DOCKER_HOME=$(HOME)
    DOCKER_SOCKET=/var/run/docker.sock
endif

all: create_postgres_data_dir up help

# Configurar Docker rootless en Linux
configure-rootless:
ifeq ($(UNAME_S),Linux)
	@echo "$(COLOR_GREEN)Configurando Docker rootless...$(COLOR_RESET)"
	@mkdir -p $(DOCKER_HOME)/.docker
	@mkdir -p /goinfre/$(USER)/docker-volumes
	@chmod 700 $(DOCKER_HOME)/.docker
	@chmod 700 /goinfre/$(USER)/docker-volumes
	@if ! command -v dockerd-rootless-setuptool.sh >/dev/null 2>&1; then \
		echo "$(COLOR_GREEN)Instalando Docker rootless...$(COLOR_RESET)"; \
		curl -fsSL https://get.docker.com/rootless | sh; \
	fi
	@dockerd-rootless-setuptool.sh install --force || true
	@systemctl --user enable docker || true
	@systemctl --user start docker || true
	@loginctl enable-linger $(USER)
endif

# Levanta los servicios definidos en el archivo de composición
up: configure-rootless
	@echo "$(COLOR_GREEN)Levantando servicios...$(COLOR_RESET)"
	@if [ "$(UNAME_S)" = "Linux" ]; then \
		export DOCKER_HOST=unix://$(DOCKER_SOCKET); \
		export XDG_RUNTIME_DIR=/run/user/$$(id -u); \
		systemctl --user start docker || true; \
		sleep 2; \
	fi
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) up -d

# Detiene y elimina los contenedores, redes y volúmenes asociados
down:
	@echo "$(COLOR_GREEN)Apagando y eliminando servicios...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) down --volumes 

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

# Reinicia los servicios (down y luego up)
reset: down up
	@echo "$(COLOR_GREEN)Reinicio completado.$(COLOR_RESET)"

# Limpia todos los contenedores detenidos, imágenes y volúmenes no utilizados
clean:
	@echo "$(COLOR_GREEN)Limpiando recursos no utilizados...$(COLOR_RESET)"
	docker system prune -f --all

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

# Regla para crear directorio de db
create_postgres_data_dir:
	@if [ ! -d "./srcs/postgres_data" ]; then \
        mkdir -p ./srcs/postgres_data; \
        chmod 777 ./srcs/postgres_data; \
        echo "$(COLOR_GREEN)Directorio postgres_data creado y permisos asignados$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_YELLOW)Directorio postgres_data ya existe$(COLOR_RESET)"; \
	fi

# Regla para limpiar el directorio de datos de postgres
clean_postgres_data_dir:
	@rm -rf ./srcs/postgres_data
	@echo "$(COLOR_GREEN)Directorio postgres_data eliminado$(COLOR_RESET)"

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

fclean: close destroy-images clean-postgres-data clean-volumes
	@echo "$(COLOR_GREEN)Limpieza completa finalizada$(COLOR_RESET)"

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
	@echo "  http://localhost:8000      - Accede a la web desde Django (backend sin Nginx)"
	@echo "  http://localhost:8082      - WAF redirige a https://localhost (frontend)"
	@echo ""
	@echo "  https://localhost:8445     - WAF entrada principal al frontend <<<<<<<<<<<<<<<<===================="
	@echo ""
	@echo "  http://localhost:3000      - Acceso a front directo"
	@echo ""
	@echo "  https://localhost:8200     - Panel acceso a Vault"
	@echo "                             * Ver waf/vault/init-vault.sh para más información"
	@echo ""
	@echo "  http://localhost:8000/game            - Crea una sala y accede al juego (debes loguearte primero)"
	@echo "  http://localhost:8000/game/{id-sala} - Accede a la sala creada previamente (debes loguearte primero)"
	@echo ""
	@echo "  http://localhost:8000/api/ninja/docs  - Apis"
	@echo ""
	
.PHONY: all up down logs reset clean close debug status images help rebuild-images destroy-images check_db_tables connect_db list_databases fclean re clean view-users view-tables view-users-fields

