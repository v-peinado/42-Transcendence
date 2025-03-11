from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from .base import BaseGameConsumer
import asyncio
import json
import time
from channels.db import database_sync_to_async
import traceback
from .shared_state import game_players, game_states
from .utils.diagnostic import DiagnosticLogger as diag

class GameConsumer(BaseGameConsumer):
    async def connect(self):
        """Connect to websocket"""
        try:
            # Use base class connect method
            await super().connect()
            
            # If connection validation failed, return early
            if not hasattr(self, "game_state") or not self.game_state:
                print(f"[DEBUG] GameConsumer.connect - No game state for {self.scope['user'].username}")
                return
            
            # Importante: Usar database_sync_to_async para acceder a la base de datos
            game = await DatabaseOperations.get_game(self.game_id)
            if not game:
                print(f"[DEBUG] GameConsumer.connect - Game {self.game_id} not found")
                await self.close(code=4004)  # Custom code: Game not found
                return
                
            self.scope["game"] = game
            
            # Si el juego está en estado FINISHED, rechazamos la conexión
            if game and game.status == "FINISHED":
                print(f"[DEBUG] GameConsumer.connect - Game {self.game_id} is already finished")
                await self.close(code=4002)
                return
            
            # CORREGIDO: Ahora verificamos los IDs directamente sin acceder a relaciones
            is_valid_player = (game and (self.user.id == game.player1_id or 
                            (game.player2_id is not None and self.user.id == game.player2_id)))
            
            if is_valid_player:
                # Register the user as connected to this game
                await self.manage_connected_players(add=True)
                await MultiplayerHandler.handle_player_join(self, game)
                
                # Send game information to the client safely
                player1_info = await self._get_player_info(game.player1_id)
                player2_info = await self._get_player_info(game.player2_id) if game.player2_id else None
                
                await self.send(text_data=json.dumps({
                    "type": "game_info",
                    "player1": player1_info.get('username') if player1_info else 'Unknown',
                    "player2": player2_info.get('username') if player2_info else None,
                    "player1_id": game.player1_id,
                    "player2_id": game.player2_id,
                    "game_id": game.id,
                }))
                
                # Si la partida está en curso o finalizada, restaurar el estado
                if game.status == "PLAYING" and hasattr(self, "game_state"):
                    side = getattr(self, "side", None)
                    
                    # Marcar al consumidor como reconectando
                    self.reconnecting = True
                    
                    # MODIFICACIÓN: Restablecer el estado de la pala pero asegurarse de que esté lista para input
                    if side:
                        paddle = self.game_state.paddles.get(side)
                        if paddle:
                            print(f"[RECONNECT] Restableciendo pala para {self.user.username} ({side})")
                            # Guardar posición actual para restaurarla
                            current_y = paddle.y
                            paddle.reset_state(current_y)
                            # Asegurar que esté lista para input
                            paddle.ready_for_input = True
                    
                    # Enviar el estado actual del juego al cliente
                    player1_name = player1_info.get('username') if player1_info else 'Unknown'
                    player2_name = player2_info.get('username') if player2_info else None
                    
                    await self.send(text_data=json.dumps({
                        "type": "game_state",
                        "state": self.game_state.serialize(),
                        "is_reconnection": True,
                        "player_side": side,
                        "player1": player1_name,
                        "player2": player2_name
                    }))
                    print(f"[RECONNECT] Estado de juego enviado a {self.user.username} (lado: {side})")
                    
                    # Después de un pequeño retraso, eliminar el flag de reconexión
                    # MODIFICACIÓN: Reducir este tiempo de 1.0 segundos a 0.1 segundos
                    await asyncio.sleep(0.1)
                    self.reconnecting = False
            else:
                # Unauthorized user, close the connection
                print(f"[DEBUG] GameConsumer.connect - User {self.user.id} not a player in game {self.game_id}")
                await self.close(code=4001)
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"[DEBUG] Error en GameConsumer.connect: {error_details}")
            if not hasattr(self, 'websocket_closed'):
                await self.close(code=4500)

    @database_sync_to_async
    def _get_player_info(self, user_id):
        """Obtener información básica del jugador de forma segura"""
        if not user_id:
            return None
            
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': user.id,
                'username': user.username
            }
        except Exception:
            return None

    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        if hasattr(self, "game_state") and self.game_state:
            game = self.scope.get("game")
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)
        
        # Update game_players to mark player as disconnected
        game_id = str(self.game_id)
        if hasattr(self, 'player_side') and game_id in game_players and self.player_side in game_players[game_id]:
            game_players[game_id][self.player_side]["connected"] = False
            game_players[game_id][self.player_side]["disconnect_time"] = asyncio.get_event_loop().time()
            
            diag.info('GameConsumer', f'Player {self.user.username} ({self.player_side}) disconnected from game {game_id}')
    
    async def determine_player_side(self):
        """Determine which side (left/right) the connected player is on"""
        game = await DatabaseOperations.get_game(self.game_id)
        if not game:
            return None
        
        if game.player1 and game.player1.id == self.user.id:
            return "left"
        elif game.player2 and game.player2.id == self.user.id:
            return "right"
        return None

    async def receive(self, text_data):
        """Receive message from websocket (string)"""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        """Receive message from websocket (dictionary)"""
        message_type = content.get("type")
        
        # Manejar pings de diagnóstico
        if message_type == "ping":
            # Responder al ping inmediatamente para medir la latencia
            timestamp = content.get("timestamp")
            connection_id = content.get("connectionId")
            await self.send(text_data=json.dumps({
                "type": "pong",
                "client_timestamp": timestamp,
                "server_timestamp": int(time.time() * 1000),
                "connection_id": connection_id
            }))
            return
            
        # OPTIMIZACIÓN: Fast reconnect protocol
        if message_type == "fast_reconnect":
            if hasattr(self, "game_state") and self.game_state:
                # Obtener directamente el lado del jugador de la solicitud
                player_side = content.get("side") or getattr(self, "side", None)
                player_id = content.get("player_id")
                
                # Verificar que el jugador tiene permiso para este lado
                if player_side and player_id and str(player_id) == str(self.user.id):
                    # Establecer el lado si no estaba ya establecido
                    if not hasattr(self, "side") or not self.side:
                        self.side = player_side
                        diag.info('GameConsumer', f'Fast reconnect: Lado establecido para {self.user.username}: {player_side}')
                    
                    # Resetear el estado de la pala sin esperas
                    paddle = self.game_state.paddles.get(player_side)
                    if paddle:
                        diag.info('GameConsumer', f'Fast reconnect: Reseteando pala para {self.user.username} ({player_side})')
                        current_y = paddle.y
                        paddle.reset_state(current_y)
                        paddle.ready_for_input = True  # Asegurar que está listo para input
                    
                    # Enviar estado inmediatamente sin serializar todo el juego
                    current_state = {
                        "type": "fast_state",
                        "ball": {
                            "x": self.game_state.ball.x,
                            "y": self.game_state.ball.y,
                            "speed_x": self.game_state.ball.speed_x,
                            "speed_y": self.game_state.ball.speed_y,
                            "radius": self.game_state.ball.radius
                        },
                        "paddles": {
                            "left": {
                                "x": self.game_state.paddles["left"].x,
                                "y": self.game_state.paddles["left"].y,
                                "width": self.game_state.paddles["left"].width,
                                "height": self.game_state.paddles["left"].height,
                                "moving": self.game_state.paddles["left"].moving,
                                "direction": self.game_state.paddles["left"].last_direction,
                            },
                            "right": {
                                "x": self.game_state.paddles["right"].x,
                                "y": self.game_state.paddles["right"].y,
                                "width": self.game_state.paddles["right"].width,
                                "height": self.game_state.paddles["right"].height,
                                "moving": self.game_state.paddles["right"].moving,
                                "direction": self.game_state.paddles["right"].last_direction,
                            }
                        },
                        "score": {
                            "left": self.game_state.paddles["left"].score,
                            "right": self.game_state.paddles["right"].score
                        },
                        "status": self.game_state.status,
                        "player_side": player_side,
                        "timestamp": int(time.time() * 1000)
                    }
                    
                    # Notificar que el jugador se ha reconectado
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "player_reconnected",
                            "side": player_side,
                            "player_id": self.user.id,
                            "username": self.user.username
                        }
                    )
                    
                    # Enviar respuesta rápida
                    await self.send(text_data=json.dumps(current_state))
                    diag.info('GameConsumer', f'Fast reconnect completado para {self.user.username} ({player_side})')
                    return
        
        if message_type == "move_paddle":
            await GameStateHandler.handle_paddle_movement(self, content)
        elif message_type == "ready_for_countdown":
            # Player is ready for countdown
            if hasattr(self, "game_state") and self.game_state:
                self.game_state.player_ready = True
                if not hasattr(self.game_state, "countdown_started") or not self.game_state.countdown_started:
                    self.game_state.countdown_started = True
                    asyncio.create_task(GameStateHandler.countdown_timer(self))
        elif message_type == "request_game_state":
            # Client is requesting the game state (reconnection)
            if hasattr(self, "game_state") and self.game_state:
                # Establecer flag de reconexión
                self.reconnecting = True
                
                # Identificar el lado del jugador para incluirlo en la respuesta
                player_side = getattr(self, "side", None)
                
                # If the side is not set, try to determine it
                if not player_side:
                    game = self.scope.get("game")
                    if game:
                        if game.player1_id and self.user.id == game.player1_id:
                            player_side = "left"
                            self.side = "left"
                            diag.info('GameConsumer', f'Lado determinado para reconexión: {player_side} (player1)')
                        elif game.player2_id and self.user.id == game.player2_id:
                            player_side = "right"
                            self.side = "right"
                            diag.info('GameConsumer', f'Lado determinado para reconexión: {player_side} (player2)')
                
                # Resetear el estado de la pala para este jugador si está reconectando
                if player_side and self.game_state.status == 'playing':
                    paddle = self.game_state.paddles.get(player_side)
                    if paddle:
                        diag.info('GameConsumer', f'Reseteando pala para {self.user.username} ({player_side})')
                        # Guardar posición actual para no "teletransportar" la pala
                        current_y = paddle.y
                        paddle.reset_state(current_y)
                        paddle.ready_for_input = True
                
                # NUEVO: Usar método específico para sincronización de reconexión
                await GameStateHandler.handle_reconnection_state_sync(self)
                
                diag.info('GameConsumer', f'Estado de juego enviado a {self.user.username} (lado: {player_side})')
                
                # OPTIMIZACIÓN: Eliminar retraso después de reconexión
                self.reconnecting = False

    async def game_start(self, event):
        """Send game start event to client"""
        if self.game_state:
            await self.game_state.start_countdown()

        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """ Game loop multiplayer game"""
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        """Send game state update to client"""
        await self.send(
            text_data=json.dumps({"type": "game_state", "state": event["state"]})
        )
        
    async def player_disconnected(self, event):
        """Notify the client that a player has disconnected"""
        await self.send(
            text_data=json.dumps({
                "type": "player_disconnected",
                "side": event["side"],
                "player_id": event["player_id"]
            })
        )
        
    async def player_reconnected(self, event):
        """Notify the client that a player has reconnected """
        await self.send(
            text_data=json.dumps({
                "type": "player_reconnected",
                "side": event["side"],
                "player_id": event["player_id"],
                "username": event["username"]
            })
        )
        
    async def game_finished(self, event):
        """Send game finished event to client"""
        await self.send(text_data=json.dumps(event))
        
    async def send_current_game_state(self):
        """Send the current game state to the client"""
        # Check if we have a game state
        if hasattr(self, 'game_state') and self.game_state:
            # Prepare a state update for reconnection
            state_data = self.game_state.serialize()
            
            # Mark this as a reconnection state
            state_data['reconnection'] = True
            
            # Send directly to this client only
            await self.send_json({
                'type': 'game_state',
                'state': state_data
            })
            
            diag.info('GameConsumer', f'Sent current game state to reconnected player {self.user.username}')
        else:
            diag.warn('GameConsumer', f'No game state available to send to reconnected player {self.user.username}')
