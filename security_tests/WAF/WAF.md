# Apuntes de WAF (Web Application Firewall)

## 1. Direcciones de Vault

- **API Address** (http://0.0.0.0:8200)
  - Punto de entrada principal para interactuar con Vault
  - Accesible localmente como http://localhost:8200
  - Usada para operaciones API (secretos, políticas, etc.)

- **Cluster Address** (https://0.0.0.0:8201)
  - Puerto para comunicación entre nodos Vault
  - Usado para replicación y alta disponibilidad
  - En desarrollo solo se usa un nodo

## 2. Verificación del Sistema

- **Verificar estado de Vault**
  ```bash
  curl http://localhost:8200/v1/sys/health
  ```

- **Verificar acceso con token**
  ```bash
  curl -H "X-Vault-Token: myroot" http://localhost:8200/v1/sys/mounts
  ```

## 3. Comandos útiles desde el Makefile

- **Ver logs de WAF/Vault**
  ```bash
  make logs
  ```

- **Ver estado de contenedores**
  ```bash
  make status
  ```

- **Reiniciar servicios**
  ```bash
  make re
  ```

## 4. Pruebas de Almacenamiento

- **Guardar un secreto**
  ```bash
  curl -H "X-Vault-Token: myroot" -H "Content-Type: application/json" -X POST -d '{"data":{"test":"123"}}' http://localhost:8200/v1/secret/data/test
  ```

- **Leer el secreto**
  ```bash
  curl -H "X-Vault-Token: myroot" http://localhost:8200/v1/secret/data/test
  ```

## 5. Pruebas de XSS (Cross-Site Scripting)

Para probar la protección contra XSS, podemos intentar varios payloads:

- **XSS Básico en campos de texto**:
  ```html
  <script>alert('xss')</script>
  <img src="x" onerror="alert('xss')">
  javascript:alert('xss')
  ```

- **XSS en URL**:
  ```url
  https://localhost:8445/search?q=<script>alert('xss')</script>
  ```

- **XSS en campos de formulario (ejemplo login)**:
  ```html
  username="><script>alert('xss')</script>
  password="><img src=x onerror=alert('xss')>
  ```

Las respuestas esperadas del WAF:
- Código 403 Forbidden
- Mensaje en logs: `/var/log/modsecurity/audit.log`
- Regla activada: `REQUEST-941-APPLICATION-ATTACK-XSS.conf`

Para verificar si el WAF bloqueó el ataque:
```bash
tail -f /var/log/modsecurity/audit.log | grep "XSS"
```

## 6. Protección Rate Limiting y XSS

El sistema implementa múltiples capas de seguridad:

- **Rate Limiting en Login**:
  ```text
  - Límite: 5 intentos
  - Tiempo de bloqueo: 900s (15 minutos)
  - Mensajes de log:
    * "Rate limit increment for [IP] on login: X/5"
    * "Rate limit exceeded for [IP] on login. Blocking for 900s"
  ```

- **Ejemplos de logs de seguridad**:
  ```text
  # Intento de XSS detectado
  Failed login attempt for user <script>alert('xss')</script> from IP [IP]

  # Rate limiting activado
  Rate limit exceeded for IP [IP] on login
  ```

- **Verificación de protecciones**:
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

## 7. Pruebas de Seguridad en APIs

### Test de XSS en endpoints de API:
  ```bash
  # Test en login
  curl -k POST https://localhost:8445/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<script>alert(1)</script>","password":"test"}'

  # Test en registro
  curl -k -X POST https://localhost:8445/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<img src=x onerror=alert(1)>","email":"test@test.com","password":"test123"}'

  # Test en actualización de perfil
  curl -k -X PUT https://localhost:8445/api/user/profile/ \
  -H "Authorization: Bearer <token>" \
  -d '{"username":"<script>alert(1)</script>"}'
  ```

- **Test de SQL Injection**:
  ```bash
  # Test en login
  curl -k -X POST https://localhost:8445/api/login/ \
  -d '{"username":"admin'; DROP TABLE users; --","password":"test"}'

  # Test en búsqueda
  curl -k https://localhost:8445/api/users/search?q=1%27%20OR%20%271%27=%271
  ```

- **Test de Command Injection**:
  ```bash
  # Test en campos de texto
  curl -k -X POST https://localhost:8445/api/user/profile/ \
  -d '{"username":"|ls -la|"}'
  ```

- **Test de File Upload**:
  ```bash
  # Intento de subir archivo malicioso
  curl -k -X POST https://localhost:8445/api/user/profile/image \
  -F "file=@malicious.php"

  # Intento de bypass de tipo MIME
  curl -k -X POST https://localhost:8445/api/user/profile/image \
  -F "file=@shell.php;type=image/jpeg"
  ```

- **Monitoreo de respuestas**:
  ```bash
  # Ver logs en tiempo real
  tail -f /var/log/modsecurity/audit.log

  # Filtrar por tipo de ataque
  grep "XSS" /var/log/modsecurity/audit.log
  grep "SQLI" /var/log/modsecurity/audit.log
  grep "COMMAND" /var/log/modsecurity/audit.log
  ```

- **Respuestas esperadas del WAF**:
  - 403 Forbidden: Ataque detectado
  - 400 Bad Request: Payload malformado
  - Logs en `/var/log/modsecurity/audit.log`
  - Headers de seguridad en respuesta

- **Endpoints críticos a probar**:
  ```text
  /api/login/
  /api/register/
  /api/user/profile/
  /api/chat/messages/
  /api/game/create/
  /api/tournament/create/
  /api/friends/add/
  ```

- **Verificación de protecciones**:
  ```bash
  # Ver ataques bloqueados
  docker exec srcs-waf-1 cat /var/log/modsecurity/audit.log | grep "403"

  # Ver reglas activadas
  docker exec srcs-waf-1 cat /var/log/modsecurity/debug.log | grep "Rule"
  ```

## 8. Entendiendo los Logs del WAF

Los logs del WAF se encuentran en `/var/log/modsecurity/audit.log` y `/var/log/modsecurity/debug.log`. Aquí hay algunos ejemplos de cómo interpretar los logs:

- **Detección de XSS**:
  ```log
  [error] ModSecurity: Access denied with code 403 (phase 2). Matched "Operator `Contains' with parameter `<script'" against variable `REQUEST_BODY' (Value: `{"username":"<script>alert('xss')</script>","password":"<img src=\"x\" onerror=\"alert('xss')\">"}') [file "/etc/nginx/modsecurity/rules/main.conf"] [line "209"] [id "1000003"] [msg "Potential XSS Attack Detected"] [data "Matched Data: {\x22username\x22:\x22<script>alert('xss')</script>\x22,\x22password\x22:\x22<img src=\x5c\x22x\x5c\x22 onerror=\x5c\x22alert('xss')\x5c\x22>\x22}"] [severity "2"] [tag "attack-xss"]
  ```

- **Detección de SQL Injection**:
  ```log
  [error] ModSecurity: Access denied with code 403 (phase 2). Matched "Operator `Contains' with parameter `DROP TABLE'" against variable `REQUEST_BODY' (Value: `{"username":"admin'; DROP TABLE users; --","password":"test"}') [file "/etc/nginx/modsecurity/rules/main.conf"] [line "210"] [id "1000004"] [msg "Potential SQL Injection Attack Detected"] [data "Matched Data: admin'; DROP TABLE users; --"] [severity "2"] [tag "attack-sqli"]
  ```

- **Detección de Command Injection**:
  ```log
  [error] ModSecurity: Access denied with code 403 (phase 2). Matched "Operator `Contains' with parameter `|ls -la|'" against variable `REQUEST_BODY' (Value: `{"username":"|ls -la|"}') [file "/etc/nginx/modsecurity/rules/main.conf"] [line "211"] [id "1000005"] [msg "Potential Command Injection Attack Detected"] [data "Matched Data: |ls -la|"] [severity "2"] [tag "attack-command"]
  ```

Estos logs muestran:
- El tipo de ataque detectado
- El payload malicioso
- La regla que se activó
- El código de respuesta (403 Forbidden)

Para monitorear los logs en tiempo real:
```bash
tail -f /var/log/modsecurity/audit.log
```

Para filtrar logs específicos:
```bash
grep "XSS" /var/log/modsecurity/audit.log
grep "SQLI" /var/log/modsecurity/audit.log
grep "COMMAND" /var/log/modsecurity/audit.log
```
