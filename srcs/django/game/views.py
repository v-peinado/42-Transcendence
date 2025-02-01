from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Game

@login_required
def menu_page(request):
    return render(request, 'game/menu.html')

@login_required
def game_page(request, game_id=None):
    mode = request.GET.get('mode', 'multi')
    
    if game_id is None:
        game = Game.objects.create(
            player1=request.user,
            status='PLAYING' if mode == 'single' else 'WAITING',  # Cambiar estado inicial según modo
            game_mode=mode.upper(),
            difficulty='medium'  # Dificultad por defecto para modo single
        )
        game_id = game.id

    context = {
        'user_id': request.user.id,
        'username': request.user.username,
        'game_id': game_id,
        'game_mode': mode
    }
    return render(request, 'game/game.html', context)