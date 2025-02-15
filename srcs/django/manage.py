#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

# Este archivo es generado automáticamente por Django al crear un proyecto.
# Importa el módulo de Django y ejecuta la función execute_from_command_line() con sys.argv como argumento.
# sys.argv es una lista de argumentos pasados al script de Python desde la línea de comandos (esta lista se genera automáticamente al ejecutar un script).
# El primer argumento es el nombre del script, y el segundo es el comando a ejecutar.
# Por ejemplo, si se ejecuta 'python manage.py runserver', sys.argv será ['manage.py', 'runserver'].
# Por lo tanto, execute_from_command_line(['manage.py', 'runserver']) ejecutará el comando 'runserver' de Django.
# Basicamente, este archivo es el punto de entrada para ejecutar comandos de Django desde la línea de comandos de forma programática.

