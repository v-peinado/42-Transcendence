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
        
        print(f"Conectando jugador {self.user.username} al juego {self.game_id}")  # Debug
        
        # Inicializar game_state inmediatamente para ambos jugadores
        self.game_state = GameState()
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        game = await self.get_game()
        if game:
            game_player1 = await self.get_player1(game)
            game_player2 = await self.get_player2(game)
            
            # Si es el jugador 1, iniciar game_loop
            if game.player1 == self.user:
                self.game_state.status = 'playing'
                asyncio.create_task(self.game_loop())
                
            # Si es el segundo jugador
            elif game.status == 'WAITING' and game_player1 != self.user and not game_player2:
                await self.update_game(game)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_start',
                        'player1': game_player1.username,
                        'player2': self.user.username
                    }
                )

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
        print(f"Mensaje recibido en el consumer: {content}")  # Debug
        
        if content.get('type') == 'move_paddle':
            side = content.get('side')
            direction = content.get('direction')
            print(f"Procesando movimiento: lado={side}, dirección={direction}")  # Debug
            
            if hasattr(self, 'game_state'):
                print(f"Estado del juego antes del movimiento: {self.game_state.serialize()}")  # Debug
                self.game_state.move_paddle(side, direction)
                print(f"Estado del juego después del movimiento: {self.game_state.serialize()}")  # Debug
                
                # Enviar actualización inmediata
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_state_update',
                        'state': self.game_state.serialize()
                    }
                )
            else:
                print("Error: game_state no está inicializado")  # Debug

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
        """Enviar actualización del estado del juego al cliente"""
        print(f"Enviando actualización de estado: {event}")  # Debug
        await self.send_json({
            'type': 'game_state',
            'state': event['state']
        })