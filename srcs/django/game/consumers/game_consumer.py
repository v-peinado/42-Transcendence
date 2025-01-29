from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Game
from ..engine.game_state import GameState
import json
import asyncio

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.user = self.scope['user']
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        game = await self.get_game()
        if game:
            if game.status == 'WAITING':
                # Verificar jugadores de forma asíncrona
                player1 = await self.get_player1(game)
                player2 = await self.get_player2(game)
                
                if player1 != self.user and not player2:
                    # Actualizar juego de forma asíncrona
                    await self.update_game(game)
                    
                    # Notificar inicio del juego
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'game_start',
                            'player1': player1.username,
                            'player2': self.user.username
                        }
                    )

            if game.status == 'PLAYING':
                self.game_state = GameState()
                self.game_state.status = 'playing'
                asyncio.create_task(self.game_loop())

    @database_sync_to_async
    def get_game(self):
        try:
            return Game.objects.get(id=self.game_id)
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def get_player1(self, game):
        return game.player1

    @database_sync_to_async
    def get_player2(self, game):
        return game.player2

    @database_sync_to_async
    def update_game(self, game):
        game.player2 = self.user
        game.status = 'PLAYING'
        game.save()

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

    async def game_start(self, event):
        """Maneja el evento de inicio del juego"""
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Loop principal del juego"""
        while True:
            if hasattr(self, 'game_state') and self.game_state.status == 'playing':
                self.game_state.update()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_state_update',
                        'state': self.game_state.serialize()
                    }
                )
            await asyncio.sleep(1/60)  # 60 FPS

    async def game_state_update(self, event):
        """Enviar actualización del estado del juego"""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': event['state']
        }))