from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            'matchmaking',
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            'matchmaking',
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Implementar lógica de matchmaking