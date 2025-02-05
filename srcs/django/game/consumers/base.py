from channels.generic.websocket import AsyncJsonWebsocketConsumer

class BaseGameConsumer(AsyncJsonWebsocketConsumer):
    game_states = {}

    async def connect(self):
        """Conectar al websocket"""
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.user = self.scope['user']
        self.game_state = None
        self.player_side = None

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Desconectar del websocket"""
        if hasattr(self, 'game_id') and self.game_id in self.game_states:
            del self.game_states[self.game_id]

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
