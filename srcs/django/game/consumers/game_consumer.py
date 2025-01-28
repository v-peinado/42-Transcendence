from channels.generic.websocket import AsyncJsonWebsocketConsumer
from ..engine.game_state import GameState
import json
import asyncio

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Iniciar el estado del juego
        self.game_state = GameState()
        
        # Iniciar el loop del juego
        asyncio.create_task(self.game_loop())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Implementar lógica de recepción de datos

    async def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        message_type = content.get('type')
        
        if message_type == 'move_paddle':
            side = content.get('side')
            direction = content.get('direction')
            if side in ['left', 'right']:
                self.game_state.move_paddle(side, direction)
                
        elif message_type == 'start_game':
            self.game_state.game_status = 'playing'
            
        elif message_type == 'pause_game':
            self.game_state.game_status = 'paused'

    async def game_loop(self):
        while True:
            self.game_state.update()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_state_update',
                    'state': self.game_state.__dict__
                }
            )
            await asyncio.sleep(1/60)  # 60 FPS

    async def game_state_update(self, event):
        """Send game state to WebSocket"""
        await self.send_json(event['state'])