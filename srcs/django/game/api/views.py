from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Game
from .engine.game_state import GameState

@login_required
def create_game(request):
    """Crea una nueva partida y devuelve su ID"""
    game = Game.objects.create(
        player1=request.user,
        status='WAITING'
    )
    return JsonResponse({
        'game_id': game.id,
        'status': 'created'
    })

@login_required
def join_game(request, game_id):
    """Une a un jugador a una partida existente"""
    try:
        game = Game.objects.get(id=game_id, status='WAITING')
        if game.player1 != request.user and not game.player2:
            game.player2 = request.user
            game.status = 'PLAYING'
            game.save()
            
            # Notificar a través de WebSocket que el juego puede comenzar
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'game_{game_id}',
                {
                    'type': 'game_start',
                    'game_id': game_id,
                    'player1': game.player1.username,
                    'player2': game.player2.username
                }
            )
            
            return JsonResponse({
                'status': 'joined',
                'game_id': game_id
            })
    except Game.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Game not found or already full'
        }, status=404)

@login_required
def game_status(request, game_id):
    """Obtiene el estado actual de una partida"""
    try:
        game = Game.objects.get(id=game_id)
        return JsonResponse({
            'status': game.status,
            'player1': game.player1.username,
            'player2': game.player2.username if game.player2 else None,
            'score_player1': game.score_player1,
            'score_player2': game.score_player2
        })
    except Game.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Game not found'
        }, status=404)

@login_required
def game_page(request, game_id=None):
    """Renderiza la página del juego"""
    return render(request, 'game/game.html', {
        'game_id': game_id,
        'user_id': request.user.id,
        'username': request.user.username
    })