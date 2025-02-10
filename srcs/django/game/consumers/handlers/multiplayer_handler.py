import asyncio
from channels.db import database_sync_to_async
from django.db import transaction

class MultiplayerHandler:
    """Maneja la lógica específica del modo multijugador"""

    @staticmethod
    async def handle_player_join(consumer, game):
        """Iniciar o unirse a juego multijugador"""
        
        if game.status == 'WAITING':
            # Obtener player1 de forma asíncrona
            player1 = await database_sync_to_async(getattr)(game, 'player1')
            
            if player1 == consumer.user:
                consumer.side = 'left'
            else:
                consumer.side = 'right'
                
                @database_sync_to_async
                def update_game():
                    with transaction.atomic():
                        game.refresh_from_db()
                        game.player2 = consumer.user
                        game.status = 'PLAYING'
                        game.save()
                    return game

                await update_game()
                
                # Notificar inicio del juego a todos los jugadores
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
        else:
            # Obtener player2 de forma asíncrona
            player2 = await database_sync_to_async(getattr)(game, 'player2')
            consumer.side = 'right' if player2 and player2 == consumer.user else 'left'

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Maneja la desconexión de un jugador"""
        if hasattr(consumer, 'side'):
            winner_side = 'right' if consumer.side == 'left' else 'left'
            consumer.game_state.status = 'finished'
            
            @database_sync_to_async
            def update_game_on_disconnect():
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
                    'reason': 'desertion',
                    'deserter': consumer.side,
                    'final_score': {
                        'left': consumer.game_state.paddles['left'].score,
                        'right': consumer.game_state.paddles['right'].score
                    }
                }
            )
