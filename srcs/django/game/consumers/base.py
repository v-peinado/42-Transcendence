from channels.generic.websocket import AsyncJsonWebsocketConsumer
from ..engine.game_state import GameState
import json

class BaseGameConsumer(AsyncJsonWebsocketConsumer):
    game_states = {}

    async def connect(self):
        """Connect to websocket"""
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = f"game_{self.game_id}"
        self.user = self.scope["user"]
        self.game_state = await self.initialize_game_state()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        if hasattr(self, "game_id") and self.game_id in self.game_states:
            del self.game_states[self.game_id]

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def initialize_game_state(self):
        """Centralize game state initialization"""
        if self.game_id not in self.game_states:
            self.game_states[self.game_id] = GameState()
        return self.game_states[self.game_id]

    async def game_finished(self, event):
        """Send game end message"""
        await self.send(text_data=json.dumps(event))
