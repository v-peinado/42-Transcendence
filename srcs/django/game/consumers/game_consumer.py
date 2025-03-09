from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from .shared_state import connected_players
from .base import BaseGameConsumer
import asyncio
import json

class GameConsumer(BaseGameConsumer):
    async def connect(self):
        """Connect to websocket"""
        self.user = self.scope["user"]
        
        # Verify that the user is connected from only one place
        if self.user.id in connected_players:
            existing_channel = connected_players[self.user.id]
            if existing_channel != self.channel_name:
                # User is already connected from another place, reject this connection
                await self.close(code=4000)
                return
        
        await super().connect()
        
        game = await DatabaseOperations.get_game(self.game_id)
        self.scope["game"] = game
        
        # Verify that the user is authorized to join this game
        if game and (self.user.id == game.player1.id or self.user.id == game.player2.id):
            # Register the user as connected to this game
            connected_players[self.user.id] = self.channel_name
            await MultiplayerHandler.handle_player_join(self, game)
        else:
            # Unauthorized user, close the connection
            await self.close(code=4001)

    async def disconnect(self, close_code):
        # Verify that the user is connected to this game before disconnecting
        if hasattr(self, 'user') and self.user.id in connected_players and connected_players[self.user.id] == self.channel_name:
            del connected_players[self.user.id]
        
        # Handle player disconnection
        if self.game_state:
            game = await DatabaseOperations.get_game(self.game_id)
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
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
        if self.game_state:
            await self.game_state.start_countdown()

        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        await self.send(
            text_data=json.dumps({"type": "game_state", "state": event["state"]})
        )
