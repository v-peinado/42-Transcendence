from channels.db import database_sync_to_async
import json
import asyncio
from .base import BaseGameConsumer
from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from ..models import Game

class GameConsumer(BaseGameConsumer):
    """Main game consumer that coordinates different handlers"""

    async def connect(self):
        await super().connect()

        @database_sync_to_async
        def get_game():
            return Game.objects.select_related("player1", "player2").get(
                id=self.game_id
            )

        game = await get_game()
        self.scope["game"] = game

        if game:
            await MultiplayerHandler.handle_player_join(self, game)

    async def disconnect(self, close_code):
        if self.game_state:
            game = await DatabaseOperations.get_game(self.game_id)
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        """Receive message"""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        """Receive JSON message"""
        message_type = content.get("type")

        if message_type == "move_paddle":
            await GameStateHandler.handle_paddle_movement(self, content)

    async def game_start(self, event):
        """Start game from server"""
        if self.game_state:
            await self.game_state.start_countdown()
            asyncio.create_task(GameStateHandler.countdown_timer(self))
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Main game loop"""
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        """Send game state update"""
        await self.send(
            text_data=json.dumps({"type": "game_state", "state": event["state"]})
        )
