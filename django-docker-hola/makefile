# Nombre del archivo de composición de Docker por defecto
COMPOSE_FILE = docker-compose.yml

# Variables de colores para los mensajes
COLOR_GREEN = \033[0;32m
COLOR_RESET = \033[0m

# Levanta los servicios definidos en docker-compose.yml
up:
	@echo "$(COLOR_GREEN)Levantando servicios...$(COLOR_RESET)"
	docker-compose -f $(COMPOSE_FILE) up -d

# Detiene y elimina los contenedores, redes y volúmenes asociados
down:
	@echo "$(COLOR_GREEN)Apagando y eliminando servicios...$(COLOR_RESET)"
	docker-compose -f $(COMPOSE_FILE) down

# Muestra los logs de los contenedores
logs:
	@echo "$(COLOR_GREEN)Mostrando logs...$(COLOR_RESET)"
	docker-compose -f $(COMPOSE_FILE) logs -f

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

# Ejecuta docker-compose up sin el modo de detach (para depurar)
debug:
	@echo "$(COLOR_GREEN)Ejecutando en modo de depuración...$(COLOR_RESET)"
	docker-compose -f $(COMPOSE_FILE) up

# Muestra el estado de los contenedores
status:
	@echo "$(COLOR_GREEN)Mostrando estado de los contenedores...$(COLOR_RESET)"
	docker-compose -f $(COMPOSE_FILE) ps

# Ayuda para ver las reglas disponibles
help:
	@echo "Reglas disponibles:"
	@echo "  make up       - Levanta los servicios en modo detach"
	@echo "  make down     - Detiene y elimina los servicios"
	@echo "  make logs     - Muestra los logs en tiempo real"
	@echo "  make reset    - Reinicia los servicios (down + up)"
	@echo "  make clean    - Limpia contenedores, imágenes y volúmenes no utilizados"
	@echo "  make close    - Apaga servicios y ejecuta prune"
	@echo "  make debug    - Levanta los servicios sin detach para depuración"
	@echo "  make status   - Muestra el estado de los contenedores"
	@echo "  make help     - Muestra esta ayuda"

.PHONY: up down logs reset clean close debug status help
