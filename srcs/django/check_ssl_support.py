#!/usr/bin/env python3
"""
Verifica si el cliente Python puede usar SSL con PostgreSQL
"""
import sys
import ssl
import socket
import psycopg2
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

def print_colored(text, color):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

print_colored("=== Diagnóstico de soporte SSL en Python ===", 'green')

# Verificar versión de OpenSSL
print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
print(f"Default SSL protocol: {ssl.PROTOCOL_TLS}")

# Verificar protocolos disponibles
print("\nSSL/TLS protocols available:")
for protocol in ['TLSv1', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']:
    try:
        proto_constant = getattr(ssl, f'PROTOCOL_{protocol}')
        print(f"- {protocol}: Available")
    except AttributeError:
        print(f"- {protocol}: Not available")

# Verificar si psycopg2 puede ser importado con éxito
print("\nChecking psycopg2 installation:")
try:
    print(f"psycopg2 version: {psycopg2.__version__}")
    print_colored("✅ psycopg2 installed correctly", 'green')
except Exception as e:
    print_colored(f"❌ Error with psycopg2: {e}", 'red')

# Verificar si Django está configurado correctamente
from django.conf import settings

print("\nDjango database configuration:")
try:
    db_config = settings.DATABASES['default']
    print(f"ENGINE: {db_config['ENGINE']}")
    print(f"HOST: {db_config['HOST']}")
    print(f"PORT: {db_config['PORT']}")
    if 'OPTIONS' in db_config:
        print("OPTIONS:")
        for key, value in db_config['OPTIONS'].items():
            if key != 'password':
                print(f"  {key}: {value}")
    print_colored("✅ Django database settings found", 'green')
except Exception as e:
    print_colored(f"❌ Error in Django database settings: {e}", 'red')

# Verificar conexión SSL al servidor PostgreSQL
print("\nTesting SSL connection to PostgreSQL server:")
db_host = settings.DATABASES['default']['HOST']
db_port = int(settings.DATABASES['default']['PORT'])

try:
    # Check TCP connection first
    sock = socket.create_connection((db_host, db_port), timeout=5)
    sock.close()
    print_colored(f"✅ TCP connection successful to {db_host}:{db_port}", 'green')
    
    # Now try SSL handshake
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # Skip certificate verification for testing
    
    sock = socket.create_connection((db_host, db_port), timeout=5)
    ssl_sock = context.wrap_socket(sock, server_hostname=db_host)
    print_colored(f"✅ SSL handshake successful: {ssl_sock.version()}", 'green')
    ssl_sock.close()
except Exception as e:
    print_colored(f"❌ SSL connection error: {e}", 'red')

print_colored("\nDiagnóstico completo", 'green')
