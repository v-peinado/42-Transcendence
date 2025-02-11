import asyncio
from channels.db import database_sync_to_async
from django.db import transaction

class GameStateHandler:
    """Actualizaciones de estado del juego"""
    
    @staticmethod
    async def handle_paddle_movement(consumer, content):
        """Maneja el movimiento de la pala"""
        side = content.get('side')															# Lado del jugador
        direction = content.get('direction', 0)												# Dirección del movimiento de la pala (0 = quieto, 1 = arriba, -1 = abajo)
        
        if hasattr(consumer, 'game_state') and consumer.game_state:							# Comprueba que hay un juego en curso y un estado de juego
            consumer.game_state.move_paddle(side, direction)								# Mueve la pala con
            
            await consumer.channel_layer.group_send(										# Envía un mensaje de actualización del estado del juego
                consumer.room_group_name,
                {
                    'type': 'game_state_update',											# Definimos el tipo de mensaje como 'game_state_update'
                    'state': consumer.game_state.serialize()								# Serializamos el estado del juego y lo enviamos
                }
            )

    @staticmethod
    async def game_loop(consumer):															# Loop principal del juego
        """Loop principal del juego"""
        while consumer.game_state.status == 'playing':
            winner = consumer.game_state.update(asyncio.get_event_loop().time())			# Actualiza el estado del juego y comprueba si hay un ganador
            
            if winner:																		# Si hay un ganador...
                @database_sync_to_async														# Actualiza el ganador del juego en la base de datos
                def update_game_winner():
                    with transaction.atomic():												# Asegura que la operación se realice de forma atómica (todo o nada)
                        game = consumer.scope["game"]										# Obtiene el juego actual
                        game.refresh_from_db()												# Refresca el objeto del juego desde la base de datos
                        game.status = 'FINISHED'											# Establece el estado del juego como 'FINISHED'
                        if winner == 'left':												# Si el ganador es el jugador de la izquierda...
                            game.winner = game.player1
                            game.score_player1 = consumer.game_state.paddles['left'].score
                            game.score_player2 = consumer.game_state.paddles['right'].score
                        else:																# Si el ganador es el jugador de la derecha...
                            game.winner = game.player2
                            game.score_player1 = consumer.game_state.paddles['left'].score
                            game.score_player2 = consumer.game_state.paddles['right'].score
                        game.save()
                
                await update_game_winner()													# Await para la actualización del ganador del juego
                
                await consumer.channel_layer.group_send(									# Enviamos un mensaje de finalización del juego
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
                break																		# Salimos del loop si hay un ganador

            await consumer.channel_layer.group_send(										# Enviamos un mensaje de actualización del estado del juego al otro jugador
                consumer.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': consumer.game_state.serialize()
                }
            )
            await asyncio.sleep(1/60)														# Esperamos 1/60 segundos antes de la siguiente iteración (60 FPS)

    @staticmethod
    async def countdown_timer(consumer):													# Temporizador de cuenta atrás
        """Maneja la cuenta atrás del juego"""
        countdown_value = 3
        
        while countdown_value > 0:
            consumer.game_state.countdown = countdown_value									# Actualiza el valor de la cuenta atrás
            state = consumer.game_state.serialize()											# Serializa el estado del juego
            
            await consumer.channel_layer.group_send(										# Envía un mensaje de actualización del estado del juego
                consumer.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': state
                }
            )
            
            await asyncio.sleep(1)															# Esto es para que los numeros se muestran cada segundo
            countdown_value -= 1															# Decrementa el valor de la cuenta atrás
        
        # Una vez terminada la cuenta atrás, se inicia el juego
        consumer.game_state.countdown_active = False
        consumer.game_state.countdown = 0
        consumer.game_state.status = 'playing'
        
        # Seteamos la posición de la pelota cada vez que se inicia el juego
        consumer.game_state.ball.reset(
            consumer.game_state.CANVAS_WIDTH / 2,
            consumer.game_state.CANVAS_HEIGHT / 2
        )
        
        # Enviar estado del juego actualizado una vez que se inicia el juego
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {
                'type': 'game_state_update',
                'state': consumer.game_state.serialize()
            }
        )
        
        # Iniciar el loop del juego
        asyncio.create_task(GameStateHandler.game_loop(consumer))
