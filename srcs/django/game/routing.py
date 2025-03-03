from django.urls import re_path, path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .consumers.game_consumer import GameConsumer
from .consumers.matchmaking_consumer import MatchmakingConsumer

websocket_urlpatterns = [
    re_path(r"ws/game/(?P<game_id>\w+)/$", GameConsumer.as_asgi()),
    path('ws/matchmaking/', MatchmakingConsumer.as_asgi()),
]
application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
