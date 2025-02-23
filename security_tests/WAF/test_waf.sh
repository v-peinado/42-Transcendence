#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Base URL
BASE_URL="https://localhost:8445"

# Function to print test results
print_result() {
    if [ $1 -eq 403 ]; then
        echo -e "${GREEN}✓ Attack blocked (403 Forbidden)${NC}"
    else
        echo -e "${RED}✗ Attack not blocked (Status: $1)${NC}"
    fi
}

echo -e "${YELLOW}=== Starting WAF Security Tests ===${NC}"

echo -e "\n${YELLOW}1. Testing XSS Attacks${NC}"

# Test XSS in login (múltiples vectores)
echo "Testing XSS in login (script tag)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"<script>alert(1)</script>","password":"test"}')
print_result $STATUS

echo "Testing XSS in login (img tag)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"<img src=x onerror=alert(1)>","password":"test"}')
print_result $STATUS

echo "Testing XSS in login (javascript protocol)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"javascript:alert(1)//","password":"test"}')
print_result $STATUS

# Test XSS en registro (múltiples vectores)
echo "Testing XSS in registration (basic)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/register/" \
-H "Content-Type: application/json" \
-d '{"username":"<img src=x onerror=alert(1)>","email":"test@test.com","password1":"test123","password2":"test123"}')
print_result $STATUS

echo "Testing XSS in registration (encoded)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/register/" \
-H "Content-Type: application/json" \
-d '{"username":"%3Cscript%3Ealert(1)%3C/script%3E","email":"test@test.com","password1":"test123","password2":"test123"}')
print_result $STATUS

echo -e "\n${YELLOW}2. Testing SQL Injection Attacks${NC}"

# Test SQL Injection básico
echo "Testing SQL Injection (basic)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"admin\"; DROP TABLE users; --","password":"test"}')
print_result $STATUS

# Test SQL Injection UNION
echo "Testing SQL Injection (UNION)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/login/" \
-H "Content-Type: application/json" \
-d '{"username":"admin\" UNION SELECT * FROM users--","password":"test"}')
print_result $STATUS

# Test SQL Injection en URL
echo "Testing SQL Injection in URL (OR)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/users/search?q=1%27%20OR%20%271%27=%271")
print_result $STATUS

echo "Testing SQL Injection in URL (UNION)..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/users/search?q=1%27%20UNION%20SELECT%20*%20FROM%20users--")
print_result $STATUS

echo -e "\n${YELLOW}3. Testing File Upload Attacks${NC}"

# Crear archivos de prueba
echo "<?php system(\$_GET['cmd']); ?>" > malicious.php
echo "alert('xss')" > malicious.js
echo "<script>alert(1)</script>" > malicious.html
echo "DROP TABLE users;" > malicious.sql

# Test varios tipos de archivos maliciosos
for file in malicious.php malicious.js malicious.html malicious.sql; do
    echo "Testing upload of $file..."
    STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/user/profile/image" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$file")
    print_result $STATUS
done

# Test bypass MIME type
echo "Testing MIME type bypass..."
STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/user/profile/image" \
-H "Content-Type: multipart/form-data" \
-F "file=@malicious.php;type=image/jpeg" \
-F "filename=image.jpg")
print_result $STATUS

# Limpiar archivos de prueba
rm -f malicious.*
