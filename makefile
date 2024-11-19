# Detectar el sistema operativo
OS := $(shell uname -s)

# Definir rutas según el sistema operativo
ifeq ($(OS), Linux)
    DJANGO_CODE_PATH := $(HOME)/goinfre/django
    DJANGO_MEDIA_PATH := $(HOME)/goinfre/django/media
    POSTGRES_DATA_PATH := $(HOME)/goinfre/postgres_data
    NGINX_FRONTEND_PATH := $(HOME)/goinfre/nginx/frontend
else ifeq ($(OS), Darwin)
    DJANGO_CODE_PATH := $(PWD)/srcs/django
    DJANGO_MEDIA_PATH := $(PWD)/srcs/django/media
    POSTGRES_DATA_PATH := $(PWD)/srcs/postgres_data
    NGINX_FRONTEND_PATH := $(PWD)/srcs/nginx/frontend
endif

# Exportar variables para docker-compose
export DJANGO_CODE_PATH
export DJANGO_MEDIA_PATH
export POSTGRES_DATA_PATH
export NGINX_FRONTEND_PATH

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

all: up help

# Crear directorios necesarios para Django media
create-media-dirs:
	@echo "$(COLOR_GREEN)Creando directorios para media...$(COLOR_RESET)"
	@mkdir -p $(DJANGO_MEDIA_PATH)/profile_images
	@chmod 777 $(DJANGO_MEDIA_PATH)/profile_images

# Levanta los servicios definidos en el archivo de composición
up: create-media-dirs
	@echo "$(COLOR_GREEN)Levantando servicios...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) up -d

# Detiene y elimina los contenedores, redes y volúmenes asociados
down:
	@echo "$(COLOR_GREEN)Apagando y eliminando servicios...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) down --volumes

# Limpia volúmenes de datos de PostgreSQL
clean-postgres-data:
	@echo "$(COLOR_GREEN)Verificando si existe el volumen de datos de postgres para eliminar...$(COLOR_RESET)"
	@if docker volume inspect postgres_data > /dev/null 2>&1; then \
		echo "$(COLOR_GREEN)Eliminando volumen de datos de postgres...$(COLOR_RESET)"; \
		docker volume rm -f postgres_data; \
	else \
		echo "$(COLOR_GREEN)No hay volumen de datos de postgres para eliminar.$(COLOR_RESET)"; \
	fi

# Limpia los volúmenes y directorios media
clean-volumes:
	@echo "$(COLOR_RED)Eliminando volúmenes y archivos media...$(COLOR_RESET)"
	@rm -rf $(DJANGO_MEDIA_PATH)/profile_images/* 2>/dev/null || true
	@docker volume rm -f django_media postgres_data || true

# Limpia recursos no utilizados
clean:
	@echo "$(COLOR_GREEN)Limpiando recursos no utilizados...$(COLOR_RESET)"
	docker system prune -f --all

# Apaga servicios y ejecuta prune
close: down
	@echo "$(COLOR_GREEN)Ejecutando prune tras apagar servicios...$(COLOR_RESET)"
	docker system prune -f

# Limpia completamente contenedores, imágenes y datos persistentes
fclean: close destroy-images clean-postgres-data clean-volumes
	@echo "$(COLOR_RED)Eliminando carpetas y rutas creadas...$(COLOR_RESET)"
	@rm -rf srcs/django/media/profile_images 2>/dev/null || true
	@echo "$(COLOR_GREEN)Limpieza completa finalizada$(COLOR_RESET)"


# Limpia y reinicia
re: fclean all

# Reinicia los servicios (down + up)
reset: down up

# Ejecuta docker compose up sin modo detach
debug:
	@echo "$(COLOR_GREEN)Ejecutando en modo de depuración...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) up

# Muestra el estado de los contenedores
status:
	@echo "$(COLOR_GREEN)Mostrando estado de los contenedores...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) ps

# Muestra logs de los contenedores
logs:
	@echo "$(COLOR_GREEN)Mostrando logs...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) logs -f

# Muestra un resumen de las imágenes
images:
	@echo "$(COLOR_GREEN)Mostrando imágenes de Docker...$(COLOR_RESET)"
	docker images

# Reconstruye todas las imágenes
rebuild-images:
	@echo "$(COLOR_GREEN)Reconstruyendo todas las imágenes de Docker...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) build

# Destruye todas las imágenes
destroy-images:
	@echo "$(COLOR_GREEN)Destruyendo todas las imágenes de Docker...$(COLOR_RESET)"
	docker rmi -f $$(docker images -q) || true
	docker image prune -a -f

# Comprueba tablas en la base de datos
check_db_tables:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB) -c "\dt"

# Conecta a la base de datos
connect_db:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB)

# Lista bases de datos
list_databases:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) -c "\l"

# Muestra los usuarios de la base de datos
view-users:
	@echo "Conectando a la base de datos PostgreSQL y mostrando todos los campos de los usuarios..."
	@docker exec -it postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT * FROM authentication_customuser;"

# Ayuda
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
	@echo "  make clean-volumes         - Limpia volúmenes y medios"
	@echo "  make view-users            - Muestra los usuarios autorizados en la base de datos"
	@echo ""
	@echo "  para ver la web desde django, accede a http://localhost:8000"
	@echo "  para ver la web desde nginx, accede a http://localhost:80"
	@echo ""

.PHONY: all up down logs reset clean close debug status images help rebuild-images destroy-images check_db_tables connect_db list_databases fclean re clean-volumes view-users
