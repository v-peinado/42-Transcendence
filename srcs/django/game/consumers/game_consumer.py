from ..engine.game_state import GameState
import json
import asyncio
from .base import BaseGameConsumer
from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from channels.db import database_sync_to_async
from ..models import Game

class GameConsumer(BaseGameConsumer):
    """Consumidor principal del juego que coordina los diferentes handlers"""
    game_states = {}                                                 # Diccionario de estados de juego compartidos

    async def connect(self):
        await super().connect()
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        
        @database_sync_to_async
        def get_game():
            return Game.objects.select_related('player1', 'player2').get(id=self.game_id)

        game = await get_game()
        self.scope["game"] = game  # Guardar el juego en el scope
        
        if game:
            await self.initialize_game_state()
            await MultiplayerHandler.handle_player_join(self, game)

    async def initialize_game_state(self):
        """Inicializa el estado del juego si no existe"""
        if self.game_id not in self.game_states:
            self.game_states[self.game_id] = GameState()
        self.game_state = self.game_states[self.game_id]

    async def disconnect(self, close_code):
        if self.game_state:
            game = await DatabaseOperations.get_game(self.game_id)
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        """Recibir mensaje"""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        """Recibir mensaje JSON"""
        message_type = content.get('type')
        
        if message_type == 'move_paddle':
            await GameStateHandler.handle_paddle_movement(self, content)

    async def game_start(self, event):
        """Iniciar el juego desde el servidor"""
        if self.game_state:
            await self.game_state.start_countdown()  # Añadir await aquí
            asyncio.create_task(GameStateHandler.countdown_timer(self))
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Loop principal del juego"""
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        """Enviar actualización del estado del juego"""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': event['state']
        }))

    async def game_finished(self, event):
        """Enviar mensaje de fin de juego"""
        await self.send(text_data=json.dumps(event))