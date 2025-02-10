from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Game

@login_required
def game_view(request, game_id=None):
    """Vista unificada para crear/unirse a juegos"""
    if game_id is None:
        game = Game.objects.create(
            player1=request.user,
            status='WAITING',
            game_mode='MULTI'
        )
    else:
        try:
            game = Game.objects.get(id=game_id)
            if game.status != 'WAITING' or game.player1 == request.user:
                return redirect('game:create_game')
        except Game.DoesNotExist:
            return redirect('game:create_game')

    return render(request, 'game/game.html', {
        'game_id': game.id,
        'game_mode': 'multi',
        'user_id': request.user.id
    })