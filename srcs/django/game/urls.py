from django.urls import path
from .views import GameModesView, MatchmakingView, GameView
from . import views

app_name = "game"

urlpatterns = [
    path("", GameModesView.as_view(), name="game_modes_view"),
    path("matchmaking/", MatchmakingView.as_view(), name="matchmaking_view"),
    path("game/<int:game_id>/", GameView.as_view(), name="game_view"),
    path('single_player/', views.single_player_view, name='single_player_view'), # Borrar esta línea
    path('multi_player/', views.multi_player_view, name='multi_player_view'), # Borrar esta línea
]