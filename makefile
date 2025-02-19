# Variables esenciales
COMPOSE_FILE = ./srcs/docker-compose.yml
COMPOSE_CMD = docker compose
COLOR_GREEN = \033[0;32m
COLOR_RESET = \033[0m

# Regla por defecto
all: up help

# Levanta los servicios
up:
	@echo "$(COLOR_GREEN)Desplegando servicios...$(COLOR_RESET)"
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) up --build

# Detiene y limpia todo (sin eliminar volúmenes)
down:
	@echo "$(COLOR_GREEN)Deteniendo servicios...$(COLOR_RESET)"
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) down

# Detiene y limpia todo (incluyendo volúmenes)
down_volumes:
	@echo "$(COLOR_GREEN)Deteniendo servicios y eliminando volúmenes...$(COLOR_RESET)"
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) down --volumes

# Limpia todos los recursos (excepto volúmenes críticos)
clean:
	@echo "$(COLOR_GREEN)Limpiando recursos...$(COLOR_RESET)"
	@docker system prune -f --all
	@docker volume rm $$(docker volume ls -q | grep -v "postgres_data\|vault_data") 2>/dev/null || true
	@docker network prune -f

# Limpieza completa (preservando la base de datos)
fclean: down clean
	@echo "$(COLOR_GREEN)Limpieza completa finalizada (base de datos preservada)$(COLOR_RESET)"

# Limpieza completa (incluyendo la base de datos)
fcleandb: down_volumes clean
	@echo "$(COLOR_GREEN)Limpieza completa finalizada (incluyendo base de datos)$(COLOR_RESET)"

# Reinicio completo
re: fclean all

# Ayuda básica
help:
	@echo ""
	@echo "$(COLOR_GREEN)Comandos disponibles:$(COLOR_RESET)"
	@echo "  make                     - Despliega los servicios (equivalente a docker compose up --build)"
	@echo "  make re                  - Limpieza completa y redespliega todo"
	@echo "  make down                - Detiene todos los servicios"
	@echo "  make clean               - Limpia todos los recursos (imágenes, contenedores, volúmenes y redes)"
	@echo "  make fclean              - Limpieza completa (detiene, limpia y elimina todos los recursos)"
	@echo "  make fcleandb            - Limpieza completa (detiene, limpia y elimina todos los recursos, incluyendo la base de datos)"
	@echo ""
	@echo "$(COLOR_GREEN)Accesos:$(COLOR_RESET)"
	@echo "  https://localhost:8445     - WAF entrada principal al frontend <<<<<<<<<<<<<<<<===================="
	@echo "  http://localhost:8082      - WAF redirige a https://localhost (frontend)"
	@echo "  http://localhost:3000      - Acceso directo al frontend"
	@echo "  http://localhost:8000      - Acceso directo al backend"
	@echo "  https://localhost:8200     - Panel acceso a Vault"
	@echo "                            * Ver waf/vault/init-vault.sh para más información"
	@echo ""
	@echo "  http://localhost:8000/game           - Crea una sala y accede al juego (debes loguearte primero)"
	@echo "  http://localhost:8000/game/{id-sala} - Accede a la sala creada previamente (debes loguearte primero)"
	@echo ""
	@echo "  http://localhost:8000/api/ninja/docs - Apis"
	@echo ""

.PHONY: all up down clean fclean re help down_volumes fcleandb
