from .views import GameModesView, MatchmakingView, GameView
from django.urls import path

app_name = "game"

urlpatterns = [
    path("", GameModesView.as_view(), name="game_modes_view"),
    path("matchmaking/", MatchmakingView.as_view(), name="matchmaking_view"),
    path("game/<int:game_id>/", GameView.as_view(), name="game_view"),
]