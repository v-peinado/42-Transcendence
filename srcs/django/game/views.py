from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views import View
from .models import Game

User = get_user_model()

@login_required
def single_player_view(request):
    return render(request, 'game/single_player.html')

@login_required
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

@method_decorator(login_required, name='dispatch')
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
