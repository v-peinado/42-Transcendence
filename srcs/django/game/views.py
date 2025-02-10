from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Game

@login_required
def create_game(request):
    """Crear una nueva partida"""
    game = Game.objects.create(
        player1=request.user,
        status='WAITING',
        game_mode='MULTI'
    )
    return render(request, 'game/game.html', {
        'game_id': game.id,
        'game_mode': 'multi',
        'user_id': request.user.id
    })

@login_required
def join_game(request, game_id):
    """Unirse a una partida existente"""
    try:
        game = Game.objects.get(id=game_id)
        if game.status == 'WAITING' and game.player1 != request.user:
            return render(request, 'game/game.html', {
                'game_id': game_id,
                'game_mode': 'multi',
                'user_id': request.user.id
            })
    except Game.DoesNotExist:
        return redirect('game:create_game')
    
    return redirect('game:create_game')