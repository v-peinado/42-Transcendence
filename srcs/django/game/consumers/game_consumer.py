from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from .base import BaseGameConsumer
import asyncio
import json

class GameConsumer(BaseGameConsumer):
    async def connect(self):
        """Connect to websocket"""
        # Use base class connect method
        await super().connect()
        
        # If connection validation failed, return early
        if not hasattr(self, "game_state"):
            return
        
        game = await DatabaseOperations.get_game(self.game_id)
        self.scope["game"] = game
        
        # Si el juego está en estado FINISHED, rechazamos la conexión
        if game and game.status == "FINISHED":
            await self.close(code=4002)
            return
        
        # We verify that the user is a original player of the game
        is_valid_player = (game and (self.user.id == game.player1.id or self.user.id == game.player2.id))
        
        if is_valid_player:
            # Register the user as connected to this game
            await self.manage_connected_players(add=True)
            await MultiplayerHandler.handle_player_join(self, game)
            
            # Send game information to the client so they can display it correctly in case of reconnection
            await self.send(text_data=json.dumps({
                "type": "game_info",
                "player1": game.player1.username,
                "player2": game.player2.username if game.player2 else None,
                "player1_id": game.player1.id,
                "player2_id": game.player2.id if game.player2 else None,
                "game_id": game.id,
            }))
            
            # If the game is in PLAYING state, send the game state to the client for reconnection
            if game.status == "PLAYING" and hasattr(self, "game_state"):
                side = getattr(self, "side", None)
                await self.send(text_data=json.dumps({
                    "type": "game_state",
                    "state": self.game_state.serialize(),
                    "is_reconnection": True,
                    "player_side": side,
                    "player1": game.player1.username,
                    "player2": game.player2.username if game.player2 else None
                }))
                print(f"Estado de juego enviado a {self.user.username} (lado: {side})")
        else:
            # Unauthorized user, close the connection
            await self.close(code=4001)

    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        if hasattr(self, "game_state") and self.game_state:
            game = self.scope.get("game")
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        """Receive message from websocket (string)"""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        """Receive message from websocket (dictionary)"""
        message_type = content.get("type")
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
                # Identificar el lado del jugador para incluirlo en la respuesta
                player_side = getattr(self, "side", None)
                
                # If the side is not set, try to determine it
                if not player_side:
                    game = self.scope.get("game")
                    if game and game.player1 and game.player2:
                        if self.user.id == game.player1.id:
                            player_side = "left"
                            self.side = "left"
                        elif self.user.id == game.player2.id:
                            player_side = "right"
                            self.side = "right"
                
                # Get the game object
                game = self.scope.get("game")
                
                # Send the game state to the client
                await self.send(text_data=json.dumps({
                    "type": "game_state", 
                    "state": self.game_state.serialize(),
                    "is_reconnection": True,
                    "player_side": player_side,
                    "player1_id": game.player1.id if game and game.player1 else None,
                    "player2_id": game.player2.id if game and game.player2 else None,
                    "player1": game.player1.username if game and game.player1 else None,
                    "player2": game.player2.username if game and game.player2 else None
                }))
                
                print(f"Estado de juego enviado a {self.user.username} (lado: {player_side})")

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
