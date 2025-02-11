import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Conectar al websocket"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Desconectar del websocket"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def game_finished(self, event):
        """Enviar mensaje de fin de juego al websocket"""
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'winner': event['winner'],
            'reason': event['reason'],
            'final_score': event['final_score']
        }))
