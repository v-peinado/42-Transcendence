"""
WSGI config for main project.

Web Server Gateway Interface (WSGI) 
is a specification for simple and universal interface between web servers 
and web applications or frameworks for the Python programming language.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

application = get_wsgi_application()
