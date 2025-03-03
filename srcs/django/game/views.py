from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import Game
from django.contrib.auth import get_user_model

User = get_user_model()

waiting_players = []


def single_player_view(request):
    return render(request, 'game/single_player.html')


def multi_player_view(request):
    return render(request, 'game/multi_player.html')

@method_decorator(login_required, name='dispatch')
class GameModesView(View):
    def get(self, request):
        """View to select game mode"""
        return render(request, "game/game_modes.html")

@method_decorator(login_required, name='dispatch')
class MatchmakingView(View):
    def get(self, request):
        """View to handle matchmaking"""
        return render(request, "game/matchmaking.html")

class GameView(View):
    def get(self, request, game_id=None):
        """Unified view for creating/joining games"""
        if game_id is None:  # If there's no game ID...
            return redirect('game:game_modes_view')  # Redirect to game modes selection
        else:  # If there's a game ID...
            try:
                game = Game.objects.get(id=game_id)  # Extract the game ID
                if game.status == "FINISHED":  # If game is finished...
                    return redirect("game:game_modes_view")  # ...redirect to game modes selection
                elif game.status == "WAITING":  # If game is waiting for players...
                    return redirect("game:matchmaking_view")  # ...redirect to matchmaking
            except Game.DoesNotExist:  # If game not found...
                return redirect("game:game_modes_view")  # ...redirect to game modes selection

        return render(
            request,
            "game/game.html",
            {"game_id": game.id, "user_id": request.user.id},  # Render the game template
        )

# @method_decorator(login_required, name='dispatch')
# class ChallengeFriendView(View):
#     def get(self, request, friend_id):
#         """View to challenge a friend to a game"""
#         user = request.user
#         friend = get_object_or_404(User, id=friend_id)
#         game = Game.objects.create(player1=user, player2=friend, status='WAITING')
#         return redirect('game:game_view', game_id=game.id)