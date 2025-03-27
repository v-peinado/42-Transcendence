# Variables esenciales
COMPOSE_FILE = ./docker-compose.yml
COMPOSE_CMD = docker compose
COLOR_GREEN = \033[0;32m
COLOR_RED = \033[0;31m
COLOR_RESET = \033[0m

# Variables de entorno del archivo .env
-include srcs/.env
export $(shell sed 's/=.*//' srcs/.env 2>/dev/null)

# Regla por defecto
all: up help

# Levanta los servicios
up:
	@echo "$(COLOR_GREEN)Desplegando servicios...$(COLOR_RESET)"
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) up --build -d

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
	@docker volume rm $$(docker volume ls -q | grep -v "postgres_data\|vault_data\|django_media") 2>/dev/null || true
	@docker network prune -f

# Limpieza completa (preservando la base de datos)
fclean: down clean
	@echo "$(COLOR_GREEN)Limpieza completa finalizada (base de datos preservada)$(COLOR_RESET)"

# Limpieza completa (incluyendo la base de datos)
fcleandb: down_volumes clean
	@echo "$(COLOR_GREEN)Eliminando volumen de imágenes de perfil...$(COLOR_RESET)"
	@docker volume rm transcendence_42_django_media 2>/dev/null || true
	@echo "$(COLOR_GREEN)Limpieza completa finalizada (incluyendo base de datos y archivos de media)$(COLOR_RESET)"

# Reinicio completo
re: fclean all

# Muestra todos los usuarios de la base de datos 
view-users:
	@echo "$(COLOR_GREEN)Consultando usuarios en la base de datos...$(COLOR_RESET)"
	@if [ "$$(docker ps -q -f name=db)" ]; then \
		if docker exec $$(docker ps -q -f name=db) pg_isready >/dev/null 2>&1; then \
			echo "\n$(COLOR_GREEN)Lista de usuarios:$(COLOR_RESET)"; \
			docker exec -e PGPASSWORD="$(POSTGRES_PASSWORD)" $$(docker ps -q -f name=db) psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" \
				-c "SELECT u.id, u.username, \
						CASE \
							WHEN u.username LIKE 'deleted_user_%' THEN 'anonymized@deleted.local' \
							WHEN u.email LIKE 'gAAAAAB%' THEN 'Enc: ' || substr(u.email, 1, 20) || '...' \
							ELSE u.email \
						END as email_info, \
						substr(u.password, 1, 20) || '...' as password_hash, \
						u.is_active \
						FROM authentication_customuser u \
						ORDER BY u.id;" || \
				( \
					echo "$(COLOR_RED)Error: No se pudo consultar la base de datos$(COLOR_RESET)" \
				); \
		else \
			echo "$(COLOR_RED)Error: La base de datos no está lista$(COLOR_RESET)"; \
		fi \
	else \
		echo "$(COLOR_RED)Error: Base de datos no encontrada. Ejecuta 'make up' primero.$(COLOR_RESET)"; \
	fi

# Muestra la estructura de la tabla CustomUser
view-table:
	@echo "$(COLOR_GREEN)Consultando estructura de la tabla authentication_customuser...$(COLOR_RESET)"
	@if [ "$$(docker ps -q -f name=db)" ]; then \
		if docker exec $$(docker ps -q -f name=db) pg_isready >/dev/null 2>&1; then \
			echo "\n$(COLOR_GREEN)Estructura de la tabla:$(COLOR_RESET)"; \
			docker exec -e PGPASSWORD="$(POSTGRES_PASSWORD)" $$(docker ps -q -f name=db) psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" \
				-c "\d+ authentication_customuser;" || \
			( \
				echo "$(COLOR_RED)Error: No se pudo consultar la base de datos$(COLOR_RESET)" \
			); \
		else \
			echo "$(COLOR_RED)Error: La base de datos no está lista$(COLOR_RESET)"; \
		fi \
	else \
		echo "$(COLOR_RED)Error: Base de datos no encontrada. Ejecuta 'make up' primero.$(COLOR_RESET)"; \
	fi

# Elimina un usuario de la base de datos por ID o nombre de usuario
delete-user:
	@echo "$(COLOR_GREEN)Eliminando usuario de la base de datos...$(COLOR_RESET)"
	@echo "Introduce el ID o nombre de usuario a eliminar:"
	@read USER_IDENTIFIER; \
	if [ "$$(docker ps -q -f name=db)" ]; then \
		if docker exec $$(docker ps -q -f name=db) pg_isready >/dev/null 2>&1; then \
			if [[ "$$USER_IDENTIFIER" =~ ^[0-9]+$$ ]]; then \
				echo "$(COLOR_GREEN)Eliminando usuario con ID: $$USER_IDENTIFIER...$(COLOR_RESET)"; \
				docker exec -e PGPASSWORD="$(POSTGRES_PASSWORD)" $$(docker ps -q -f name=db) psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" \
					-c "DELETE FROM authentication_customuser WHERE id = $$USER_IDENTIFIER RETURNING id, username;" && \
				echo "$(COLOR_GREEN)Usuario eliminado correctamente.$(COLOR_RESET)" || \
				echo "$(COLOR_RED)Error: No se pudo eliminar el usuario o no existe.$(COLOR_RESET)"; \
			else \
				echo "$(COLOR_GREEN)Eliminando usuario con nombre: $$USER_IDENTIFIER...$(COLOR_RESET)"; \
				docker exec -e PGPASSWORD="$(POSTGRES_PASSWORD)" $$(docker ps -q -f name=db) psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" \
					-c "DELETE FROM authentication_customuser WHERE username = '$$USER_IDENTIFIER' RETURNING id, username;" && \
				echo "$(COLOR_GREEN)Usuario eliminado correctamente.$(COLOR_RESET)" || \
				echo "$(COLOR_RED)Error: No se pudo eliminar el usuario o no existe.$(COLOR_RESET)"; \
			fi; \
		else \
			echo "$(COLOR_RED)Error: La base de datos no está lista$(COLOR_RESET)"; \
		fi \
	else \
		echo "$(COLOR_RED)Error: Base de datos no encontrada. Ejecuta 'make up' primero.$(COLOR_RESET)"; \
	fi

# muestra los logs de los servicios
logs:
	@$(COMPOSE_CMD) -f $(COMPOSE_FILE) logs -f

# Ayuda básica
help:
	@echo ""
	@echo "$(COLOR_GREEN)Comandos disponibles:$(COLOR_RESET)"
	@echo "  make                     - Despliega los servicios (equivalente a docker compose up --build)"
	@echo "  make re                  - Limpieza completa y redespliega todo"
	@echo "  make down                - Detiene todos los servicios"
	@echo "  make view-users          - Muestra todos los usuarios de la base de datos"
	@echo "  make delete-user         - Elimina un usuario de la base de datos por ID o nombre de usuario"
	@echo "  make view-table          - Muestra la estructura de la tabla CustomUser"
	@echo "  make logs                - Muestra los logs de los servicios"
	@echo "  make clean               - Limpia todos los recursos (imágenes, contenedores, volúmenes y redes)"
	@echo "  make fclean              - Limpieza completa (detiene, limpia y elimina todos los recursos)"
	@echo "  make fcleandb            - Limpieza completa (detiene, limpia y elimina todos los recursos, incluyendo la base de datos)"
	@echo ""
	@echo "$(COLOR_GREEN)Accesos:$(COLOR_RESET)"
	@echo "  https://$(IP_SERVER):8445     - WAF entrada principal al frontend <<<<<<<<<<<<<<<<===================="
	@echo "  http://$(IP_SERVER):8082      - WAF redirige a https://$(IP_SERVER) (frontend)"
	@echo "  http://$(IP_SERVER):3000      - Acceso directo al frontend"
	@echo "  http://$(IP_SERVER):8000      - Acceso directo al backend"
	@echo "  https://$(IP_SERVER):8200     - Panel acceso a Vault"
	@echo "                            * Ver srcs/vault/scripts/vault-init.sh para más información"
	@echo ""
	@echo "  http://$(IP_SERVER):8000/game           - Crea una sala y accede al juego (debes loguearte primero)"
	@echo "  http://$(IP_SERVER):8000/game/{id-sala} - Accede a la sala creada previamente (debes loguearte primero)"
	@echo ""
	@echo "  http://$(IP_SERVER):8000/api/ninja/docs - Apis"
	@echo ""

.PHONY: all up down clean fclean re help down_volumes fcleandb view-users logs view-table delete-user
