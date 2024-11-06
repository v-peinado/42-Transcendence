# Nombre del archivo de composición de Docker por defecto
COMPOSE_FILE = ./srcs/docker-compose.yml

# Comando para Docker Compose (compatible con V2)
COMPOSE_CMD = docker compose

# Variables de colores para los mensajes
COLOR_GREEN = \033[0;32m
COLOR_RESET = \033[0m

# Cargar las variables del archivo .env
include srcs/.env
export $(shell cat srcs/.env | xargs)

# Levanta los servicios definidos en el archivo de composición
up:
	@echo "$(COLOR_GREEN)Levantando servicios...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) up -d

# Detiene y elimina los contenedores, redes y volúmenes asociados
down:
	@echo "$(COLOR_GREEN)Apagando y eliminando servicios...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) down

# Muestra los logs de los contenedores en tiempo real
logs:
	@echo "$(COLOR_GREEN)Mostrando logs...$(COLOR_RESET)"
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) logs -f

# Reinicia los servicios (down y luego up)
reset: down up
	@echo "$(COLOR_GREEN)Reinicio completado.$(COLOR_RESET)"

# Limpia todos los contenedores detenidos, imágenes y volúmenes no utilizados
clean:
	@echo "$(COLOR_GREEN)Limpiando recursos no utilizados...$(COLOR_RESET)"
	docker system prune -f

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

# Muestra un resumen de las imágenes de Docker
images:
	@echo "$(COLOR_GREEN)Mostrando imágenes de Docker...$(COLOR_RESET)"
	docker images

# Nombre de las imágenes
IMAGES = srcs-web

# Regla para reconstruir todas las imágenes, para cambios en dockerfile
rebuild-images:
	@echo "$(COLOR_GREEN)Rebuild all Docker images...$(COLOR_RESET)"
	@for image in $(IMAGES); do \
        echo "Rebuilding $$image..."; \
        docker build -t $$image .; \
	done

# Regla para destruir (eliminar) todas las imágenes
destroy-images:
	@echo "$(COLOR_GREEN)Destroying all Docker images...$(COLOR_RESET)"
	@for image in $(IMAGES); do \
        echo "Removing $$image..."; \
        docker rmi $$image || true; \
    done

fclean: close destroy-images

re: fclean up

# Regla principal para verificar la base de datos y las tablas
check_db_tables:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB) -c "\dt"

# Regla para conectarse a la base de datos (solo para verificar conexión)
connect_db:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB)

# Regla para listar las bases de datos
list_databases:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) exec $(SQL_HOST) psql --username=$(POSTGRES_USER) -c "\l"

# Ayuda para ver las reglas disponibles
help:
	@echo "Reglas disponibles:"
	@echo "  make up       			- Levanta los servicios en modo detach"
	@echo "  make down     			- Detiene y elimina los servicios"
	@echo "  make logs     			- Muestra los logs en tiempo real"
	@echo "  make reset    			- Reinicia los servicios (down + up)"
	@echo "  make clean    			- Limpia contenedores, imágenes y volúmenes no utilizados"
	@echo "  make close    			- Apaga servicios y ejecuta prune"
	@echo "  make debug    			- Levanta los servicios sin detach para depuración"
	@echo "  make status   			- Muestra el estado de los contenedores"
	@echo "  make images   			- Muestra un resumen de las imágenes de Docker"
	@echo "  make rebuild-images			- Reconstruye todas las imágenes"
	@echo "  make destroy-images			- Destruye todas las imágenes"
	@echo "  make fclean   			- Cierra servicios y destruye todas las imágenes"
	@echo "  make re       			- Ejecuta fclean y luego up"
	@echo "  make check_db_tables			- Verifica la base de datos y las tablas"
	@echo "  make connect_db			- Conéctate a la base de datos"
	@echo "  make list_databases			- Lista las bases de datos"
	@echo "  make help     			- Muestra esta ayuda"

.PHONY: up down logs reset clean close debug status images help rebuild-images destroy-images check_db_tables connect_db list_databases fclean re
