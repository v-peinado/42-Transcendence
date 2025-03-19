#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Base URL - update this to your actual base URL
BASE_URL="https://localhost:8445"

# Function to print test results
print_result() {
    # Códigos de respuesta que indican que se bloqueó un ataque
    # 200 - Success (solo si es una respuesta con mensaje de error o no la acción esperada)
    # 301/302/303/307/308 - Redirects (comúnmente a páginas de login)
    # 400 - Bad Request
    # 401 - Unauthorized
    # 403 - Forbidden
    # 404 - Not Found (puede ser una forma de manejar recursos no permitidos)
    # 405 - Method Not Allowed
    # 422 - Unprocessable Entity
    # 429 - Too Many Requests
    
    if [ $1 -eq 200 ]; then
        # Nota: asumimos que un 200 significa que se mostró un error o no se realizó la acción esperada
        # En un entorno real, necesitarías analizar el contenido de la respuesta
        echo -e "${RED}✗ Ataque posiblemente exitoso (Status: $1)${NC}"
    elif [ $1 -eq 302 ] || [ $1 -eq 301 ] || [ $1 -eq 303 ] || [ $1 -eq 307 ] || [ $1 -eq 308 ]; then
        echo -e "${GREEN}✓ Prueba superada (Redirección: $1)${NC}"
    elif [ $1 -eq 400 ] || [ $1 -eq 401 ] || [ $1 -eq 403 ] || [ $1 -eq 404 ] || [ $1 -eq 405 ] || [ $1 -eq 422 ] || [ $1 -eq 429 ]; then
        echo -e "${GREEN}✓ Prueba superada (Status: $1)${NC}"
    else
        echo -e "${RED}✗ Ataque no bloqueado (Status: $1)${NC}"
    fi
}

echo -e "${YELLOW}=== Iniciando Pruebas de Seguridad WAF ===${NC}"

echo -e "\n${YELLOW}1. Probando Ataques XSS${NC}"

# Test XSS in login (multiple vectors)
echo "Probando XSS en login (script tag)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"<script>alert(1)</script>","password":"test"}')
print_result $STATUS

echo "Probando XSS en login (img tag)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"<img src=x onerror=alert(1)>","password":"test"}')
print_result $STATUS

echo "Probando XSS en registro (basic)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/register/" \
-H "Content-Type: application/json" \
-d '{"username":"<img src=x onerror=alert(1)>","email":"test@test.com","password1":"test123","password2":"test123"}')
print_result $STATUS

echo -e "\n${YELLOW}2. Probando Ataques de Inyección SQL${NC}"

# Test SQL Injection in login
echo "Probando Inyección SQL en login (basic)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"admin\"; DROP TABLE users; --","password":"test"}')
print_result $STATUS

# Test SQL Injection in tournament endpoints
echo "Probando Inyección SQL en detalles de torneo..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/tournament/tournament_detail/1%27%20OR%20%271%27=%271/")
print_result $STATUS

# Test SQL Injection in dashboard endpoints
echo "Probando Inyección SQL en estadísticas de jugador..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/dashboard/player-stats-id/1%27%20UNION%20SELECT%20*%20FROM%20users--/")
print_result $STATUS

echo -e "\n${YELLOW}3. Probando Ataques de Subida de Archivos${NC}"

# Create test files
echo "<?php system(\$_GET['cmd']); ?>" > malicious.php
echo "alert('xss')" > malicious.js
echo "<script>alert(1)</script>" > malicious.html
echo "DROP TABLE users;" > malicious.sql

# We assume there might be a profile image upload endpoint
echo "Probando subida de archivos maliciosos..."
for file in malicious.php malicious.js malicious.html malicious.sql; do
    echo "Probando subida de $file..."
    STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/user/profile/image" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$file")
    print_result $STATUS
done

# Clean up test files
rm -f malicious.*

echo -e "\n${YELLOW}4. Probando Endpoints API de Torneos${NC}"

# Test creating tournament without authentication
echo "Probando creación de torneo sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/create_tournament/" \
-H "Content-Type: application/json" \
-d '{"name":"Test Tournament","max_match_points":10,"number_of_players":4,"participants":["Player1","Player2","Player3","Player4"]}')
print_result $STATUS

# Test getting pending tournaments without auth
echo "Probando obtención de torneos pendientes sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/tournament/pending_tournaments/")
print_result $STATUS

# Test starting tournament without auth
echo "Probando inicio de torneo sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/start_tournament/1/")
print_result $STATUS

# Test delete tournament without auth
echo "Probando eliminación de torneo sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/delete_tournament/1/")
print_result $STATUS

# Test determine winner without auth
echo "Probando determinación de ganador sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/determine_winner/1/")
print_result $STATUS

echo -e "\n${YELLOW}5. Probando Bypass de Autenticación${NC}"

# Test authentication bypass attempts
echo "Probando fijación de sesión..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/tournament/current_user/" \
-H "Cookie: sessionid=fake_session_id")
print_result $STATUS

# Test JWT token tampering if applicable
echo "Probando manipulación de token JWT..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/tournament/current_user/" \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c")
print_result $STATUS

echo -e "\n${YELLOW}6. Probando Endpoints API del Dashboard${NC}"

# Test dashboard endpoints
echo "Probando estadísticas de jugador sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/dashboard/player-stats/")
print_result $STATUS

echo "Probando estadísticas de jugador por ID sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/dashboard/player-stats-id/1/")
print_result $STATUS

echo "Probando endpoint de prueba API..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/dashboard/test-api/")
print_result $STATUS

echo -e "\n${YELLOW}7. Probando Endpoints API de Juego${NC}"

# Test game endpoints
echo "Probando modos de juego sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/game/")
print_result $STATUS

echo "Probando matchmaking sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/game/matchmaking/")
print_result $STATUS

echo "Probando vista de juego sin autenticación..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/game/game/1/")
print_result $STATUS

echo -e "\n${YELLOW}8. Probando Protección CSRF${NC}"

# Test CSRF protection for various endpoints
echo "Probando creación de torneo con protección CSRF (sin token)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/create_tournament/" \
-H "Content-Type: application/json" \
-d '{"name":"Test Tournament","max_match_points":10,"number_of_players":4,"participants":["Player1","Player2","Player3","Player4"]}')
print_result $STATUS

echo -e "\n${YELLOW}9. Probando Path Traversal${NC}"

# Test path traversal in game assets
echo "Probando path traversal en acceso a archivos..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/game/assets/../../etc/passwd")
print_result $STATUS

echo -e "\n${YELLOW}10. Probando Límite de Tasa${NC}"

# Test rate limiting on login endpoint
echo "Probando límite de tasa en login (múltiples solicitudes)..."
for i in {1..10}; do
    curl -k -s -o /dev/null "$BASE_URL/api/login/" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
done
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"test","password":"test"}')
echo "Resultado de prueba de límite de tasa (debería ser 429 si el límite de tasa está habilitado):"
print_result $STATUS

echo -e "\n${YELLOW}=== Pruebas de Seguridad WAF Completadas ===${NC}"