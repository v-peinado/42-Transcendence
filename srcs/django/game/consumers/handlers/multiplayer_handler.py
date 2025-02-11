import asyncio
from channels.db import database_sync_to_async
from django.db import transaction

class MultiplayerHandler:
    """Maneja la lógica específica del modo multijugador"""

    @staticmethod
    async def handle_player_join(consumer, game):
        """Iniciar o unirse a juego multijugador"""
        if game.status != 'WAITING':														# Cuando nos intentamos unir una vez que el juego ha comenzado...
            raise ValueError("No te puedes unir a un juego que ya ha comenzado")
            
        player1 = await database_sync_to_async(getattr)(game, 'player1')					# El jugador 1 es el que ha creado el juego
        
        if player1 == consumer.user:														# Si el jugador 1 es el usuario actual...
            consumer.side = 'left'
        else:																				# Si el jugador 2 es el usuario actual...
            consumer.side = 'right'
            
            @database_sync_to_async
            def update_game():
                with transaction.atomic():													# La operación se hace de forma atómica (todo o nada)
                    game.refresh_from_db()													# Refrescamos el juego desde la base de datos
                    game.player2 = consumer.user											# Se establece el jugador 2 como el usuario actual
                    game.status = 'PLAYING'													# Se establece el estado del juego como 'PLAYING'
                    game.save()																# Se guarda el juego en la base de datos
                return game																	# Retornamos el juego actualizado

            await update_game()
            
            # Notificar del inicio del juego a ambos jugadores
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_start',
                    'player1': player1.username,
                    'player2': consumer.user.username,
                    'player1_id': player1.id,
                    'player2_id': consumer.user.id
                }
            )
            
            consumer.game_state.status = 'countdown'
            await consumer.game_state.start_countdown()
            asyncio.create_task(consumer.game_loop())

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Manejamos la desconexión (deserción) de un jugador"""
        if hasattr(consumer, 'side'):
            winner_side = 'right' if consumer.side == 'left' else 'left'					# Si el jugador desconectado es el de la izquierda, el ganador es el de la derecha y viceversa
            consumer.game_state.status = 'finished'
            
            @database_sync_to_async
            def update_game_on_disconnect():												# Actualiza el juego al desconectarse uno de los jugadores
                with transaction.atomic():
                    game = consumer.scope["game"]
                    game.refresh_from_db()
                    game.status = 'FINISHED'
                    if consumer.side == 'left':
                        game.winner = game.player2
                    else:
                        game.winner = game.player1
                    game.save()
                return game

            await update_game_on_disconnect()
            
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_finished',
                    'winner': winner_side,
                    'reason': 'desertion',													# Se especifica que la razón de que haya terminado el juego es porque un jugador ha desertado
                    'deserter': consumer.side,
                    'final_score': {
                        'left': consumer.game_state.paddles['left'].score,
                        'right': consumer.game_state.paddles['right'].score
                    }
                }
            )
