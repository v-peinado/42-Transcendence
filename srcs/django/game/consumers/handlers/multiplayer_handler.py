import asyncio
from ..utils.database_operations import DatabaseOperations

class MultiplayerHandler:
    """Maneja la lógica específica del modo multijugador"""

    @staticmethod
    async def handle_player_join(consumer, game):
        await consumer.initialize_game_state()
        consumer.game_state.set_single_player(False)

        player1 = await DatabaseOperations.get_player1(game)            	# Obtener jugador 1
        player2 = await DatabaseOperations.get_player2(game)           		# Obtener jugador 2
        
        # Asignación del lado en el que jugará el usuario
        if player1 and player1.id == consumer.user.id:                  	# Si el jugador 1 es el usuario actual...
            consumer.player_side = 'left'
        elif not player2:                                               	# Si ya hay un jugador 1 y no hay un jugador 2...
            consumer.player_side = 'right'
        else:                                                           	# Si el usuario no es jugador 1 ni jugador 2...
            consumer.player_side = None                                 	# --> El usuario es un espectador

        if game.status == 'WAITING' and player1 != consumer.user and not player2:
            await DatabaseOperations.update_game(game, consumer.user)
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

        if game.status == 'PLAYING':
            consumer.game_state.status = 'playing'
            asyncio.create_task(consumer.game_loop())

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Maneja la desconexión de un jugador"""
        if consumer.player_side:
            winner_side = 'right' if consumer.player_side == 'left' else 'left'
            consumer.game_state.status = 'finished'
            
            game = await DatabaseOperations.get_game(consumer.game_id)
            if game:
                await DatabaseOperations.update_game_status(game, 'FINISHED')
                winner_id = (await DatabaseOperations.get_player2(game)).id if consumer.player_side == 'left' else (await DatabaseOperations.get_player1(game)).id
                await DatabaseOperations.update_game_winner(game, winner_id, consumer.game_state)
                
                await consumer.channel_layer.group_send(
                    consumer.room_group_name,
                    {
                        'type': 'game_finished',
                        'winner': winner_side,
                        'reason': 'desertion',
                        'deserter': consumer.player_side,
                        'final_score': {
                            'left': consumer.game_state.paddles['left'].score,
                            'right': consumer.game_state.paddles['right'].score
                        }
                    }
                )
