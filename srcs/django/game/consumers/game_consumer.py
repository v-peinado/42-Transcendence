from ..engine.game_state import GameState
import json
import asyncio
from .base import BaseGameConsumer
from .handlers.game_state_handler import GameStateHandler
from .handlers.single_player_handler import SinglePlayerHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations

class GameConsumer(BaseGameConsumer):
    """Consumidor principal del juego que coordina los diferentes handlers"""
    game_states = {}                                                 # Diccionario de estados de juego compartidos

    async def connect(self):
        await super().connect()
        game = await DatabaseOperations.get_game(self.game_id)
        
        if game:
            await self.initialize_game_state()
            
            if game.game_mode == 'SINGLE':
                await SinglePlayerHandler.handle_game_start(self, game)
            else:
                await MultiplayerHandler.handle_player_join(self, game)

    async def disconnect(self, close_code):
        if self.game_state:
            game = await DatabaseOperations.get_game(self.game_id)
            if game and game.game_mode == 'SINGLE':
                await SinglePlayerHandler.handle_player_disconnect(self)
            elif game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        """Recibir mensaje"""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        """Recibir mensaje JSON"""
        message_type = content.get('type')
        
        if message_type == 'change_difficulty' and self.game_state.is_single_player:
            await SinglePlayerHandler.handle_difficulty_change(self, content.get('difficulty'))
        elif message_type == 'move_paddle':
            await GameStateHandler.handle_paddle_movement(self, content)

    async def game_start(self, event):
        """Iniciar el juego desde el servidor"""
        if self.game_state:
            self.game_state.start_countdown()
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