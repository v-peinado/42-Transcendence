from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Game

@login_required
def game_view(request, game_id=None):	
    """Vista unificada para crear/unirse a juegos"""
    if game_id is None:														# Si no hay una ID del juego...
        game = Game.objects.create(											# ...se crea un nuevo juego
            player1=request.user,
            status='WAITING'
        )
    else:																	# Si hay una ID del juego...
        try:
            game = Game.objects.get(id=game_id)								# Extraemos la ID del juego
            if game.status != 'WAITING' or game.player1 == request.user:	# Si el juego no está esperando jugadores o el jugador ya está en el juego...
                return redirect('game:create_game')							# ...se redirige a la creación de un nuevo juego
        except Game.DoesNotExist:											# Si no se encuentra el juego...
            return redirect('game:create_game')								# ...se redirige a la creación de un nuevo juego

    return render(request, 'game/game.html', {								# Renderizamos el template del juego
        'game_id': game.id,
        'user_id': request.user.id
    })