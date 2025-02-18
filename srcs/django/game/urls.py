from django.urls import path
from .views import GameModesView, MatchmakingView, GameView #, ChallengeFriendView

app_name = "game"

urlpatterns = [
    path("", GameModesView.as_view(), name="game_modes_view"),
    path("matchmaking/", MatchmakingView.as_view(), name="matchmaking_view"),
    path("game/<int:game_id>/", GameView.as_view(), name="game_view"),
    #path("challenge/<int:friend_id>/", ChallengeFriendView.as_view(), name="challenge_friend"),
]