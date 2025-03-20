#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Base URL (update if needed)
BASE_URL="https://localhost:8445"

# Function to print test results based on status code
print_result() {
    # Codes that indicate the attack was blocked or request was refused
    # 200 - Possibly means action was not actually performed; custom evaluation needed
    # 301/302/303/307/308 - Redirect (often to login)
    # 400 - Bad Request
    # 401 - Unauthorized
    # 403 - Forbidden
    # 404 - Not Found
    # 405 - Method Not Allowed
    # 422 - Unprocessable Entity
    # 429 - Too Many Requests

    if [ $1 -eq 200 ]; then
        echo -e "${RED}✗ Attack might have succeeded (Status: $1)${NC}"
    elif [ $1 -eq 301 ] || [ $1 -eq 302 ] || [ $1 -eq 303 ] || [ $1 -eq 307 ] || [ $1 -eq 308 ]; then
        echo -e "${GREEN}✓ Test passed (Redirection: $1)${NC}"
    elif [ $1 -eq 400 ] || [ $1 -eq 401 ] || [ $1 -eq 403 ] || [ $1 -eq 404 ] || [ $1 -eq 405 ] || [ $1 -eq 422 ] || [ $1 -eq 429 ]; then
        echo -e "${GREEN}✓ Test passed (Status: $1)${NC}"
    else
        echo -e "${RED}✗ Attack not blocked (Status: $1)${NC}"
    fi
}

# Check if websocat is installed
# if ! command -v websocat &> /dev/null
# then
#     echo -e "${YELLOW}websocat is not installed. Installing...${NC}"
#     sudo apt-get update
#     sudo apt-get install -y websocat
# fi

echo -e "${YELLOW}=== Starting WAF Security Tests ===${NC}"

echo -e "\n${YELLOW}1. Testing XSS Attacks${NC}"

# XSS in login (script tag)
echo "Testing XSS in login (script tag)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"<script>alert(1)</script>","password":"test"}')
print_result $STATUS

# XSS in login (img tag)
echo "Testing XSS in login (img tag)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"<img src=x onerror=alert(1)>","password":"test"}')
print_result $STATUS

# XSS in login (javascript protocol)
echo "Testing XSS in login (javascript protocol)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"javascript:alert(1)//","password":"test"}')
print_result $STATUS

# XSS in registration (basic)
echo "Testing XSS in registration (basic)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/register/" \
-H "Content-Type: application/json" \
-d '{"username":"<img src=x onerror=alert(1)>","email":"test@test.com","password1":"test123","password2":"test123"}')
print_result $STATUS

# XSS in registration (encoded)
echo "Testing XSS in registration (encoded)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/register/" \
-H "Content-Type: application/json" \
-d '{"username":"%3Cscript%3Ealert(1)%3C/script%3E","email":"test@test.com","password1":"test123","password2":"test123"}')
print_result $STATUS

echo -e "\n${YELLOW}2. Testing SQL Injection Attacks${NC}"

# SQL Injection (basic)
echo "Testing SQL Injection (basic)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"admin\"; DROP TABLE users; --","password":"test"}')
print_result $STATUS

# SQL Injection (UNION)
echo "Testing SQL Injection (UNION)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"admin\" UNION SELECT * FROM users--","password":"test"}')
print_result $STATUS

# SQL Injection in URL (OR)
echo "Testing SQL Injection in URL (OR)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/users/search?q=1%27%20OR%20%271%27=%271")
print_result $STATUS

# SQL Injection in URL (UNION)
echo "Testing SQL Injection in URL (UNION)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/users/search?q=1%27%20UNION%20SELECT%20*%20FROM%20users--")
print_result $STATUS

# Additional SQL Injection tests (tournament and dashboard)
echo "Testing SQL Injection in tournament detail..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/tournament/tournament_detail/1%27%20OR%20%271%27=%271/")
print_result $STATUS

echo "Testing SQL Injection in dashboard (UNION)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/dashboard/player-stats-id/1%27%20UNION%20SELECT%20*%20FROM%20users--/")
print_result $STATUS

echo -e "\n${YELLOW}3. Testing File Upload Attacks${NC}"

# Create test files
echo "<?php system(\$_GET['cmd']); ?>" > malicious.php
echo "alert('xss')" > malicious.js
echo "<script>alert(1)</script>" > malicious.html
echo "DROP TABLE users;" > malicious.sql

# Upload malicious files
for file in malicious.php malicious.js malicious.html malicious.sql; do
    echo "Testing upload of $file..."
    STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/user/profile/image" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$file")
    print_result $STATUS
done

# MIME type bypass
echo "Testing MIME type bypass..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/user/profile/image" \
-H "Content-Type: multipart/form-data" \
-F "file=@malicious.php;type=image/jpeg" \
-F "filename=image.jpg")
print_result $STATUS

# Clean up
rm -f malicious.*

echo -e "\n${YELLOW}4. Testing Tournament API Endpoints${NC}"

echo "Testing create tournament without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/create_tournament/" \
-H "Content-Type: application/json" \
-d '{"name":"Test Tournament","max_match_points":10,"number_of_players":4,"participants":["Player1","Player2","Player3","Player4"]}')
print_result $STATUS

echo "Testing pending tournaments without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/tournament/pending_tournaments/")
print_result $STATUS

echo "Testing start tournament without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/start_tournament/1/")
print_result $STATUS

echo "Testing delete tournament without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/delete_tournament/1/")
print_result $STATUS

echo "Testing determine winner without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/determine_winner/1/")
print_result $STATUS

echo -e "\n${YELLOW}5. Testing Authentication Bypass${NC}"

echo "Testing session fixation..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/tournament/current_user/" \
-H "Cookie: sessionid=fake_session_id")
print_result $STATUS

echo "Testing JWT token tampering..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/tournament/current_user/" \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c")
print_result $STATUS

echo -e "\n${YELLOW}6. Testing Dashboard Endpoints${NC}"

echo "Testing player stats without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/dashboard/player-stats/")
print_result $STATUS

echo "Testing player stats by ID without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/dashboard/player-stats-id/1/")
print_result $STATUS

echo "Testing test-api endpoint..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/api/dashboard/test-api/")
print_result $STATUS

echo -e "\n${YELLOW}7. Testing Game Endpoints${NC}"

echo "Testing game modes without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/game/")
print_result $STATUS

echo "Testing matchmaking without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/game/matchmaking/")
print_result $STATUS

echo "Testing game view without authentication..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/game/game/1/")
print_result $STATUS

echo -e "\n${YELLOW}8. Testing CSRF Protection${NC}"

echo "Testing create tournament without CSRF token..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/tournament/create_tournament/" \
-H "Content-Type: application/json" \
-d '{"name":"No CSRF","max_match_points":10,"number_of_players":4,"participants":["P1","P2","P3","P4"]}')
print_result $STATUS

echo -e "\n${YELLOW}9. Testing Path Traversal${NC}"

echo "Testing path traversal attack..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/game/assets/../../etc/passwd")
print_result $STATUS

echo -e "\n${YELLOW}10. Testing Rate Limiting${NC}"

echo "Testing rate limiting on login (multiple requests)..."
for i in {1..10}; do
    curl -k -s -o /dev/null "$BASE_URL/api/login/" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
done
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"test","password":"test"}')
echo "Rate limit test result (429 expected if rate limit is enabled):"
print_result $STATUS

echo -e "\n${YELLOW}11. Testing WebSockets${NC}"


# Please only run this test if you have websocat installed

# echo "Testing WebSocket connection for matchmaking without authentication..."
# websocat --insecure "wss://localhost:8445/ws/matchmaking/" -E -1
# if [ $? -eq 0 ]; then
#     echo -e "${RED}✗ WebSocket connection for matchmaking successful${NC}"
# else
#     RESULT=$(websocat --insecure "wss://localhost:8445/ws/matchmaking/" 2>&1)
#     if [[ "$RESULT" == *"Connection refused"* ]] || [[ "$RESULT" == *"403 Forbidden"* ]]; then
#         echo -e "${GREEN}✓ WebSocket connection for matchmaking denied${NC}"
#     else
#         echo -e "${RED}✗ WebSocket connection for matchmaking failed${NC}"
#     fi
# fi

# echo "Testing WebSocket connection for game without authentication..."
# websocat --insecure "wss://localhost:8445/ws/game/1/" -E -1
# if [ $? -eq 0 ]; then
#     echo -e "${RED}✗ WebSocket connection for game successful${NC}"
# else
#     RESULT=$(websocat --insecure "wss://localhost:8445/ws/game/1/" 2>&1)
#     if [[ "$RESULT" == *"Connection refused"* ]] || [[ "$RESULT" == *"403 Forbidden"* ]]; then
#         echo -e "${GREEN}✓ WebSocket connection for game denied${NC}"
#     else
#         echo -e "${RED}✗ WebSocket connection for game failed${NC}"
#     fi
# fi

echo -e "\n${YELLOW}=== WAF Security Tests Completed ===${NC}"