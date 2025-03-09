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
        
        # Verify that the user is authorized to join this game
        if game and (self.user.id == game.player1.id or self.user.id == game.player2.id):
            # Register the user as connected to this game
            await self.manage_connected_players(add=True)
            await MultiplayerHandler.handle_player_join(self, game)
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
