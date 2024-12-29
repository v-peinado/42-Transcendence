1. - Direcciones de Vault

	API Address (http://0.0.0.0:8200)
		Punto de entrada principal para interactuar con Vault
		Accesible localmente como http://localhost:8200
		Usada para operaciones API (secretos, políticas, etc.)


	Cluster Address (https://0.0.0.0:8201)
		Puerto para comunicación entre nodos Vault
		Usado para replicación y alta disponibilidad
		En desarrollo solo se usa un nodo

2. Verificación del Sistema

	# Verificar estado de Vault
	curl http://localhost:8200/v1/sys/health


	# Verificar acceso con token
	curl \
		-H "X-Vault-Token: myroot" \
		http://localhost:8200/v1/sys/mounts


3. Comandos útiles desde el Makefile

	# Ver logs de WAF/Vault
	make logs

	# Ver estado de contenedores
	make status

	# Reiniciar servicios
	make re


4. Pruebas de Almacenamiento


	# Guardar un secreto
	curl \
		-H "X-Vault-Token: myroot" \
		-H "Content-Type: application/json" \
		-X POST \
		-d '{"data":{"test":"123"}}' \
		http://localhost:8200/v1/secret/data/test

	# Leer el secreto
	curl \
		-H "X-Vault-Token: myroot" \
		http://localhost:8200/v1/secret/data/test


Notas Importantes
	-El modo inmem significa que los datos se pierden al reiniciar
	-El token myroot es solo para desarrollo
	-Los puertos 8200/8201 deben estar accesibles
	-Version 1.13.0 es estable para desarrollo