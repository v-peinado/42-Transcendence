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


5. Pruebas de XSS (Cross-Site Scripting)

   Para probar la protección contra XSS, podemos intentar varios payloads:

   a) XSS Básico en campos de texto:
   ```
   <script>alert('xss')</script>
   <img src="x" onerror="alert('xss')">
   javascript:alert('xss')
   ```

   b) XSS en URL:
   ```
   https://localhost:8445/search?q=<script>alert('xss')</script>
   ```

   c) XSS en campos de formulario (ejemplo login):
   ```
   username="><script>alert('xss')</script>
   password="><img src=x onerror=alert('xss')>
   ```

   Las respuestas esperadas del WAF:
   - Código 403 Forbidden
   - Mensaje en logs: /var/log/modsecurity/audit.log
   - Regla activada: REQUEST-941-APPLICATION-ATTACK-XSS.conf

   Para verificar si el WAF bloqueó el ataque:
   ```bash
   tail -f /var/log/modsecurity/audit.log | grep "XSS"
   ```

6. Protección Rate Limiting y XSS

   El sistema implementa múltiples capas de seguridad:

   a) Rate Limiting en Login:
   ```
   - Límite: 5 intentos
   - Tiempo de bloqueo: 900s (15 minutos)
   - Mensajes de log:
     * "Rate limit increment for [IP] on login: X/5"
     * "Rate limit exceeded for [IP] on login. Blocking for 900s"
   ```

   b) Ejemplos de logs de seguridad:
   ```
   # Intento de XSS detectado
   Failed login attempt for user <script>alert('xss')</script> from IP [IP]

   # Rate limiting activado
   Rate limit exceeded for IP [IP] on login
   ```

   c) Verificación de protecciones:
   ```bash
   # Ver intentos de login fallidos
   docker logs django 2>&1 | grep "Failed login attempt"

   # Ver rate limiting
   docker logs django 2>&1 | grep "Rate limit"
   ```

   Las protecciones funcionan en capas:
   1. WAF (ModSecurity) - Bloqueo inicial de payloads maliciosos
   2. Django - Sanitización de inputs y rate limiting
   3. Logging - Registro detallado de intentos
