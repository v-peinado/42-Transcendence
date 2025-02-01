from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Game

@login_required
def menu_page(request):
    return render(request, 'game/menu.html')

@login_required
def game_page(request, game_id=None):
    if game_id is None:
        # Crear nueva partida
        game = Game.objects.create(
            player1=request.user,
            status='WAITING'
        )
        game_id = game.id

    context = {
        'user_id': request.user.id,
        'username': request.user.username,
        'game_id': game_id
    }
    return render(request, 'game/game.html', context)