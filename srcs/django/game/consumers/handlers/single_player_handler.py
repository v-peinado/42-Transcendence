import asyncio
from ..utils.database_operations import DatabaseOperations

class SinglePlayerHandler:
    """Maneja la lógica específica del modo single player"""

    @staticmethod
    async def handle_game_start(consumer, game):
        """Iniciar juego single player"""
        consumer.game_state.set_single_player(True, game.difficulty)
        consumer.player_side = 'left'

        if game.status == 'WAITING':
            await DatabaseOperations.update_game_status(game, 'PLAYING')
        
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {
                'type': 'game_start',
                'player1': consumer.user.username,
                'player2': 'CPU',
                'player1_id': consumer.user.id,
                'player2_id': None
            }
        )
        
        consumer.game_state.status = 'playing'
        asyncio.create_task(consumer.game_loop())

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Maneja la desconexión en modo single player"""
        consumer.game_state.status = 'finished'
        game = await DatabaseOperations.get_game(consumer.game_id)
        if game:
            await DatabaseOperations.update_game_status(game, 'FINISHED')
            await DatabaseOperations.update_game_winner(game, None, consumer.game_state)
            
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_finished',
                    'winner': 'abandoned',
                    'final_score': {
                        'left': consumer.game_state.paddles['left'].score,
                        'right': consumer.game_state.paddles['right'].score
                    }
                }
            )

    @staticmethod
    async def handle_difficulty_change(consumer, difficulty):
        """Maneja el cambio de dificultad"""
        if consumer.game_state.is_single_player and consumer.game_state.ai_controller:
            consumer.game_state.ai_controller.set_difficulty(difficulty)
