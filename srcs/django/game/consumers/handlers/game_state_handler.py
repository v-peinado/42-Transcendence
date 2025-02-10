import asyncio
from channels.db import database_sync_to_async
from django.db import transaction

class GameStateHandler:
    """Maneja las actualizaciones del estado del juego"""
    
    @staticmethod
    async def handle_paddle_movement(consumer, content):
        side = content.get('side')
        direction = content.get('direction', 0)
        
        if hasattr(consumer, 'game_state') and consumer.game_state:
            consumer.game_state.move_paddle(side, direction)
            
            # Enviar actualización inmediata del estado
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': consumer.game_state.serialize()
                }
            )

    @staticmethod
    async def game_loop(consumer):
        """Loop principal del juego"""
        print("Starting game loop")
        
        while consumer.game_state.status == 'playing':
            winner = consumer.game_state.update(asyncio.get_event_loop().time())
            
            if winner:
                print(f"Winner detected in game loop: {winner}")
                
                @database_sync_to_async
                def update_game_winner():
                    with transaction.atomic():
                        game = consumer.scope["game"]
                        game.refresh_from_db()
                        game.status = 'FINISHED'
                        if winner == 'left':
                            game.winner = game.player1
                            game.score_player1 = consumer.game_state.paddles['left'].score
                            game.score_player2 = consumer.game_state.paddles['right'].score
                        else:
                            game.winner = game.player2
                            game.score_player1 = consumer.game_state.paddles['left'].score
                            game.score_player2 = consumer.game_state.paddles['right'].score
                        game.save()
                
                await update_game_winner()
                
                # Enviar mensaje de fin de juego
                await consumer.channel_layer.group_send(
                    consumer.room_group_name,
                    {
                        'type': 'game_finished',
                        'winner': winner,
                        'reason': 'victory',
                        'final_score': {
                            'left': consumer.game_state.paddles['left'].score,
                            'right': consumer.game_state.paddles['right'].score
                        }
                    }
                )
                break

            # Enviar actualización del estado
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': consumer.game_state.serialize()
                }
            )
            await asyncio.sleep(1/60)

    @staticmethod
    async def countdown_timer(consumer):
        """Maneja la cuenta atrás del juego"""
        countdown_value = 3
        
        while countdown_value > 0:
            consumer.game_state.countdown = countdown_value
            state = consumer.game_state.serialize()
            
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': state
                }
            )
            
            await asyncio.sleep(1)
            countdown_value -= 1
        
        # Iniciar el juego después de la cuenta atrás
        consumer.game_state.countdown_active = False
        consumer.game_state.countdown = 0
        consumer.game_state.status = 'playing'
        
        # Forzar reset de la pelota con velocidad
        consumer.game_state.ball.reset(
            consumer.game_state.CANVAS_WIDTH / 2,
            consumer.game_state.CANVAS_HEIGHT / 2
        )
        
        print("Game started with ball:", {
            'position': (consumer.game_state.ball.x, consumer.game_state.ball.y),
            'speed': (consumer.game_state.ball.speed_x, consumer.game_state.ball.speed_y)
        })  # Debug
        
        # Enviar estado final
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {
                'type': 'game_state_update',
                'state': consumer.game_state.serialize()
            }
        )
        
        # Iniciar el loop del juego
        asyncio.create_task(GameStateHandler.game_loop(consumer))
