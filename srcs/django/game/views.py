from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Game

@login_required
def menu_page(request):
    """Render página de menú"""
    return render(request, 'game/menu.html')

@login_required
def difficulty_select(request):
    """Render página de selección de dificultad"""
    return render(request, 'game/difficulty_select.html')

@login_required
def game_page(request, game_id=None, difficulty=None):
    """Render página de juego"""
    mode = request.GET.get('mode', 'multi')
    if difficulty:
        mode = 'single'
    
    if game_id is None:
        game = Game.objects.create(
            player1=request.user,
            status='PLAYING' if mode == 'single' else 'WAITING',
            game_mode=mode.upper(),
            difficulty=difficulty or 'medium'
        )
        game_id = game.id

    context = {
        'user_id': request.user.id,
        'username': request.user.username,
        'game_id': game_id,
        'game_mode': mode
    }
    return render(request, 'game/game.html', context)