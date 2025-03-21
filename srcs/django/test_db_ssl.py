#!/usr/bin/env python3
"""
Script para verificar conexiones SSL a PostgreSQL desde Django

Este script prueba diferentes configuraciones para identificar
problemas de conexión SSL entre Django y PostgreSQL.
"""

import sys
import os
import django
from django.db import connections, connection, OperationalError
import psycopg2
import ssl

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

def print_colored(level, message):
    """Imprimir mensajes con colores para mejorar legibilidad"""
    colors = {
        'INFO': '\033[92m',  # Green
        'WARN': '\033[93m',  # Yellow
        'ERROR': '\033[91m', # Red
        'RESET': '\033[0m'   # Reset
    }
    print(f"{colors.get(level, '')}{level}: {message}{colors['RESET']}")

def get_connection_details():
    """Obtener detalles de configuración de conexión desde settings.py"""
    db_settings = connections.databases['default']
    print_colored('INFO', "Configuración de conexión:")
    for key, value in db_settings.items():
        if key != 'PASSWORD':  # No mostrar contraseña
            print(f"  {key}: {value}")
    
    if 'OPTIONS' in db_settings:
        print_colored('INFO', "Opciones de conexión:")
        for key, value in db_settings['OPTIONS'].items():
            print(f"  {key}: {value}")
    return db_settings

def test_django_connection():
    """Probar conexión usando Django"""
    print_colored('INFO', "Intentando conexión a través de Django ORM...")
    try:
        # Ejecutar una consulta simple
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            row = cursor.fetchone()
            print_colored('INFO', f"Conexión exitosa - PostgreSQL versión: {row[0]}")
            
            # Verificar si la conexión usa SSL
            cursor.execute("SHOW ssl;")
            ssl_status = cursor.fetchone()[0]
            print_colored('INFO', f"Estado SSL: {ssl_status}")
            
            # Verificar qué tipo de conexión estamos usando
            cursor.execute("""
                SELECT ssl, version, cipher FROM pg_stat_ssl 
                JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid 
                WHERE pg_stat_activity.pid = pg_backend_pid();
            """)
            ssl_details = cursor.fetchone()
            if ssl_details and ssl_details[0]:
                print_colored('INFO', f"✅ Conexión SSL establecida: Versión={ssl_details[1]}, Cifrado={ssl_details[2]}")
            else:
                print_colored('WARN', "⚠️ Conexión establecida pero SIN SSL")
        return True
    except OperationalError as e:
        print_colored('ERROR', f"Error de conexión (Django): {e}")
        return False

def test_direct_connection():
    """Probar conexión directa con psycopg2 y diferentes configuraciones SSL"""
    db_settings = connections.databases['default']
    
    # Modo de conexiones a probar
    ssl_modes = ['disable', 'allow', 'prefer', 'require']
    success = False
    
    for mode in ssl_modes:
        print_colored('INFO', f"Intentando conexión directa con sslmode={mode}...")
        try:
            conn = psycopg2.connect(
                dbname=db_settings['NAME'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                host=db_settings['HOST'],
                port=db_settings['PORT'],
                sslmode=mode,
                application_name=f"test_ssl_{mode}"
            )
            
            with conn.cursor() as cur:
                # Verificar si está usando SSL
                cur.execute("SHOW ssl;")
                ssl_enabled = cur.fetchone()[0]
                
                # Verificar estado de SSL para esta conexión
                cur.execute("""
                    SELECT ssl FROM pg_stat_ssl 
                    JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid 
                    WHERE pg_stat_activity.pid = pg_backend_pid();
                """)
                is_ssl = cur.fetchone()[0]
                
                if is_ssl:
                    print_colored('INFO', f"✅ Conexión exitosa con sslmode={mode} y SSL activo")
                    success = True
                else:
                    print_colored('WARN', f"⚠️ Conexión exitosa con sslmode={mode} pero SIN SSL")
                    if mode == 'require':
                        print_colored('ERROR', "SSL requerido pero no establecido - problema de configuración!")
            conn.close()
        except Exception as e:
            print_colored('ERROR', f"Error con sslmode={mode}: {e}")
    
    return success

def recommend_solutions():
    """Recomendar soluciones basadas en diagnóstico"""
    print_colored('INFO', "Recomendaciones para problemas de conexión SSL:")
    print("1. Verifica que el cliente psycopg2 está instalado con soporte SSL:")
    print("   pip install psycopg2-binary --upgrade")
    print()
    print("2. Prueba una configuración SSL mínima en settings.py:")
    print('   "OPTIONS": {"sslmode": "require"}')
    print()
    print("3. Asegúrate que los certificados estén en ubicaciones accesibles:")
    print("   - Verifica permisos: chmod 644 para .crt y 600 para .key")
    print("   - Propietario correcto: chown postgres:postgres *.crt *.key")
    print()
    print("4. Verifica disponibilidad de ssl en psycopg2:")
    print("   import ssl")
    print("   print(ssl.OPENSSL_VERSION)")
    try:
        print(f"   Versión SSL actual: {ssl.OPENSSL_VERSION}")
    except AttributeError:
        print("   No se pudo determinar versión SSL")

if __name__ == "__main__":
    print("=" * 60)
    print("Diagnóstico de conexión SSL a PostgreSQL desde Django")
    print("=" * 60)
    
    # Obtener detalles de configuración
    get_connection_details()
    print("-" * 60)
    
    # Probar conexión Django
    django_success = test_django_connection()
    print("-" * 60)
    
    # Probar conexiones directas con diferentes modos SSL
    direct_success = test_direct_connection()
    print("-" * 60)
    
    # Si hay problemas, recomendar soluciones
    if not django_success or not direct_success:
        recommend_solutions()
    
    print("=" * 60)
    print("Diagnóstico completado")
