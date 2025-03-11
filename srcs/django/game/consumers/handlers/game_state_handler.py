import asyncio
import json
import time
from ..utils.database_operations import DatabaseOperations
from ...utils.diagnostic import DiagnosticLogger as diag

class GameStateHandler:
    """Game state updates handler"""

    @staticmethod
    async def handle_paddle_movement(consumer, content):  # its async because we use await inside (is a coroutine)
        """Handle paddle movement"""
        side = content.get("side")  # Player's side
        direction = content.get("direction", 0)  # Paddle movement direction
        force_stop = content.get("force_stop", False)  # Flag to force stop
        timestamp = content.get("timestamp", 0)  # Client timestamp
        message_id = content.get("message_id", "no_id")  # Message ID for debugging
        player_id = content.get("player_id")  # ID del jugador
        
        # Mejor logging de diagnóstico
        print(f"[PADDLE] Mensaje: {message_id}, Lado: {side}, Dir: {direction}, Stop: {force_stop}, Jugador: {player_id}, TS: {timestamp}")

        # Verificar que el jugador que envía el comando es el que corresponde a este lado
        is_valid_side = False
        try:
            game = consumer.scope.get("game")
            if game:
                if side == "left" and game.player1 and game.player1.id == player_id:
                    is_valid_side = True
                elif side == "right" and game.player2 and game.player2.id == player_id:
                    is_valid_side = True
                    
            if not is_valid_side:
                print(f"[PADDLE] Comando ignorado: jugador {player_id} no puede controlar lado {side}")
                return
        except Exception as e:
            print(f"[PADDLE] Error verificando jugador: {e}")

        # Store last processed timestamp to prevent processing older messages
        if not hasattr(consumer, "last_movement_timestamp"):
            consumer.last_movement_timestamp = {}
            print(f"[PADDLE] Inicializando timestamps para {consumer.user.username}")

        # Skip outdated messages to prevent "time travel"
        if side in consumer.last_movement_timestamp:
            if timestamp < consumer.last_movement_timestamp[side]:
                print(f"[PADDLE] Ignorando mensaje antiguo para {side}. TS: {timestamp}, Último: {consumer.last_movement_timestamp[side]}")
                return
        
        # Update timestamp
        consumer.last_movement_timestamp[side] = timestamp

        if hasattr(consumer, "game_state") and consumer.game_state:
            paddle = consumer.game_state.paddles.get(side)
            
            # Si es un comando de parada forzada, reiniciar completamente el estado de la pala
            if force_stop and direction == 0:
                print(f"[PADDLE] ¡FORZANDO PARADA COMPLETA! para jugador {side}")
                
                if paddle and hasattr(paddle, "reset_state"):
                    # Un reset más agresivo que actualiza posición y estado
                    paddle.reset_state()
                    paddle.moving = False
                    paddle.last_position = paddle.y
                    paddle.target_y = paddle.y
                    paddle.ready_for_input = True  # Asegurar explícitamente que está listo para input
                    print(f"[PADDLE] Estado después del reset: {paddle.y}, moving={paddle.moving}")
                else:
                    print(f"[PADDLE] No se pudo restablecer el paddle - No existe o no tiene reset_state")
            
            # Si la pala no está lista para input y no es comando de parada, ignorar
            if paddle and not paddle.ready_for_input and not (force_stop and direction == 0):
                print(f"[PADDLE] Ignorando movimiento, pala no lista para input: {side}")
                return
            
            # IMPORTANTE: Si estamos en reconnection, asegurarse que no queden movimientos pendientes
            if hasattr(consumer, "reconnecting") and consumer.reconnecting and paddle:
                print(f"[PADDLE] Reconexión detectada - Limpiando estado de movimiento para {side}")
                paddle.moving = direction != 0
                
            # Ejecutar el movimiento en el estado del juego
            if paddle:
                if direction == 0:
                    paddle.moving = False
                    print(f"[PADDLE] Deteniendo pala {side} - moving={paddle.moving}")
                else:
                    print(f"[PADDLE] Moviendo pala {side} dir={direction}")
                
            consumer.game_state.move_paddle(side, direction)

            # Enviar actualización inmediata del estado a todos los clientes
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    "type": "game_state_update",
                    "state": consumer.game_state.serialize(),
                },
            )

    @staticmethod
    async def game_loop(consumer):
        """Main game loop"""
        while consumer.game_state.status == "playing":
            winner = consumer.game_state.update(
                asyncio.get_event_loop().time()
            )

            if winner:  # if there's a winner
                game = consumer.scope["game"]
                winner_id = game.player1.id if winner == "left" else game.player2.id
                await DatabaseOperations.update_game_winner(game, winner_id, consumer.game_state)
                await DatabaseOperations.update_game_status(game, "FINISHED")

                await consumer.channel_layer.group_send(
                    consumer.room_group_name,
                    {
                        "type": "game_finished",
                        "winner": winner,
                        "reason": "victory",
                        "final_score": {
                            "left": consumer.game_state.paddles["left"].score,
                            "right": consumer.game_state.paddles["right"].score,
                        },
                    },
                )
                break

            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {"type": "game_state_update", "state": consumer.game_state.serialize()},
            )
            await asyncio.sleep(1/60)  # 60 FPS

    @staticmethod
    async def handle_reconnection_state_sync(consumer):
        """Maneja sincronización para reconexiones"""
        if not hasattr(consumer, "game_state") or not consumer.game_state:
            print(f'No hay estado de juego para sincronizar en reconexión de {consumer.user.username}')
            return

        # 1. Obtener el estado actual
        current_state = consumer.game_state.serialize()
        
        # 2. Agregar metadatos para reconexión rápida
        current_state["fast_reconnect"] = True
        current_state["server_timestamp"] = asyncio.get_event_loop().time() * 1000
        
        # 3. Marcar el lado del jugador
        player_side = getattr(consumer, "side", None)
        
        # 4. Enviar estado para sincronización rápida
        print(f'Enviando estado para reconexión a {consumer.user.username}')
        
        # Enviar estado actual
        await consumer.send(text_data=json.dumps({
            "type": "game_state",
            "state": current_state,
            "is_reconnection": True,
            "player_side": player_side,
            "reconnection_sync": True,
            "timestamp": int(time.time() * 1000)
        }))
        
        # Enviar datos de predicción inmediatamente para mejorar la experiencia
        prediction_data = {
            "type": "game_prediction",
            "ball": {
                "x": current_state["ball"]["x"],
                "y": current_state["ball"]["y"],
                "speed_x": current_state["ball"]["speed_x"],
                "speed_y": current_state["ball"]["speed_y"]
            },
            "paddles": {
                "left": {
                    "y": current_state["paddles"]["left"]["y"],
                    "moving": current_state["paddles"]["left"].get("moving", False),
                    "direction": current_state["paddles"]["left"].get("direction", 0)
                },
                "right": {
                    "y": current_state["paddles"]["right"]["y"],
                    "moving": current_state["paddles"]["right"].get("moving", False),
                    "direction": current_state["paddles"]["right"].get("direction", 0)
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        # Enviar datos de predicción
        await consumer.send(text_data=json.dumps(prediction_data))

    @staticmethod
    async def countdown_timer(consumer):  # Countdown timer
        """Handle game countdown"""
        consumer.game_state.status = "countdown"
        consumer.game_state.countdown_active = True
        
        # Start countdown
        for countdown_value in [3, 2, 1, "GO!"]:
            consumer.game_state.countdown = countdown_value
            
            # Serialize game state and add sound indicator
            state = consumer.game_state.serialize()
            state["play_sound"] = True  # Add sound indicator
            
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {"type": "game_state_update", "state": state}
            )
            
            # Wait 1 second before next countdown value
            await asyncio.sleep(1)
        
        # Countdown finished, start game
        consumer.game_state.countdown_active = False
        consumer.game_state.countdown = None
        consumer.game_state.status = "playing"

         # Set ball position at game start with correct speed
        consumer.game_state.ball.reset(
            consumer.game_state.CANVAS_WIDTH / 2,
            consumer.game_state.CANVAS_HEIGHT / 2,
            base_speed=consumer.game_state.BALL_SPEED
        )
        
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {
                "type": "game_state_update", 
                "state": consumer.game_state.serialize(),
                "game_started": True
            }
        )

        # Start game loop in background when game starts
        asyncio.create_task(GameStateHandler.game_loop(consumer))
