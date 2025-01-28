from django.urls import re_path
from game.consumers.game_consumer import GameConsumer
from game.consumers.matchmaking_consumer import MatchmakingConsumer

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_name>\w+)/$', GameConsumer.as_asgi()),
    re_path(r'ws/matchmaking/$', MatchmakingConsumer.as_asgi()),
]