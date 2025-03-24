"""
ASGI config for main project.

Asinchronous Server Gateway Interface (ASGI) 
is a standard interface between web servers and Python applications or frameworks.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from chat.routing import websocket_urlpatterns as chat_urlpatterns
from game.routing import websocket_urlpatterns as game_urlpatterns

combined_patterns = chat_urlpatterns + game_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(combined_patterns))
        ),
    }
)
