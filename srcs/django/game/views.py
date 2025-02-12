from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Game

@login_required
def game_view(request, game_id=None):	
    """Unified view for creating/joining games"""
    if game_id is None:														# If there's no game ID...
        game = Game.objects.create(											# ...create a new game
            player1=request.user,
            status='WAITING'
        )
    else:																	# If there's a game ID...
        try:
            game = Game.objects.get(id=game_id)								# Extract the game ID
            if game.status != 'WAITING' or game.player1 == request.user:	# If game isn't waiting for players or player is already in game...
                return redirect('game:create_game')							# ...redirect to create new game
        except Game.DoesNotExist:											# If game not found...
            return redirect('game:create_game')								# ...redirect to create new game

    return render(request, 'game/game.html', {								# Render the game template
        'game_id': game.id,
        'user_id': request.user.id
    })