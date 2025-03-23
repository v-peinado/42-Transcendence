from .consumers.matchmaking_consumer import MatchmakingConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from .consumers.game_consumer import GameConsumer
from channels.auth import AuthMiddlewareStack
from django.urls import re_path

# This file is used to define the routing configuration for the Django Channels application.
# It is used to map the WebSocket URLs to the corresponding consumers.

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<game_id>\w+)/$', GameConsumer.as_asgi()),
    re_path(r'ws/matchmaking/$', MatchmakingConsumer.as_asgi()),
]
application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
