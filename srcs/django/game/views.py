from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Game

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

@login_required
def create_game(request):
    """Crea una nueva partida"""
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

            return JsonResponse({
                'status': 'joined',
                'game_id': game_id,
                'player1': game.player1.username,
                'player2': game.player2.username
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'No puedes unirte a esta partida'
            }, status=400)
    except Game.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Partida no encontrada'
        }, status=404)