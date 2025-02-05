import asyncio
from ..utils.database_operations import DatabaseOperations

class GameStateHandler:
    """Maneja las actualizaciones del estado del juego"""
    
    @staticmethod
    async def handle_paddle_movement(consumer, content):
        side = content.get('side')
        try:
            direction = int(content.get('direction', 0))
            if not -1 <= direction <= 1:                             # Si la dirección no es válida (puede ser -1, 0 o 1)...
                print(f"Invalid direction value: {direction}")
                return
                
            if side == consumer.player_side and consumer.game_state: # Si el lado es el mismo que el del jugador actual...
                current_y = consumer.game_state.paddles[side].y      # Guardar la posición actual de la paleta
                
                consumer.game_state.move_paddle(side, direction)     # Mover la paleta
                new_y = consumer.game_state.paddles[side].y        	 # Obtener la nueva posición de la paleta
                
                state = consumer.game_state.serialize()              # Serializar el estado del juego

                if current_y != new_y:                               # Solo enviar actualización si la posición cambió
                    await consumer.channel_layer.group_send(
                        consumer.room_group_name,
                        {
                            'type': 'game_state_update',
                            'state': state
                        }
                    )
        except ValueError:                                           # Si la dirección no es un número...
            print(f"Invalid direction format: {content.get('direction')}")

    @staticmethod
    async def game_loop(consumer):
        """Loop principal del juego"""
        while True:
            if (hasattr(consumer, 'game_state') and 
                consumer.game_state.status == 'playing' and 
                consumer.game_state in consumer.game_states.values()):
                
                timestamp = asyncio.get_event_loop().time()
                winner = consumer.game_state.update(timestamp)
                
                if winner:
                    game = await DatabaseOperations.get_game(consumer.game_id)
                    if game:
                        await DatabaseOperations.update_game_status(game, 'FINISHED')
                        winner_id = consumer.user.id if winner == 'left' else None if consumer.game_state.is_single_player else (await DatabaseOperations.get_player2(game)).id
                        await DatabaseOperations.update_game_winner(game, winner_id, consumer.game_state)
                    
                    await consumer.channel_layer.group_send(
                        consumer.room_group_name,
                        {
                            'type': 'game_finished',
                            'winner': winner,
                            'final_score': {
                                'left': consumer.game_state.paddles['left'].score,
                                'right': consumer.game_state.paddles['right'].score
                            }
                        }
                    )
                    break

                await consumer.channel_layer.group_send(
                    consumer.room_group_name,
                    {
                        'type': 'game_state_update',
                        'state': consumer.game_state.serialize()
                    }
                )
            await asyncio.sleep(1/60)

            if not hasattr(consumer, 'game_state') or consumer.game_state.status != 'playing':
                break

    @staticmethod
    async def countdown_timer(consumer):
        """Gestiona la cuenta regresiva antes de iniciar el juego"""
        for count in range(3, 0, -1):                              # Contar desde 3 hasta 1
            consumer.game_state.countdown = count
            
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': consumer.game_state.serialize()
                }
            )
            
            await asyncio.sleep(1.2)
            
        consumer.game_state.countdown_active = False
        consumer.game_state.status = 'playing'
        
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {
                'type': 'game_state_update',
                'state': consumer.game_state.serialize()
            }
        )
        
        asyncio.create_task(consumer.game_loop())
