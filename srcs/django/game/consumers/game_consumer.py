from channels.db import database_sync_to_async
import json
import asyncio
from .base import BaseGameConsumer
from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from ..models import Game
from .shared_state import connected_players, waiting_players

class GameConsumer(BaseGameConsumer):
    async def connect(self):
        # Obtener el usuario actual
        self.user = self.scope["user"]
        
        # Verificar si el usuario ya está conectado a un juego
        if self.user.id in connected_players:
            existing_channel = connected_players[self.user.id]
            if existing_channel != self.channel_name:
                # Usuario ya conectado desde otro lugar, rechazar la conexión
                await self.close(code=4000)
                return
        
        # Continuar con la conexión normal
        await super().connect()
        
        @database_sync_to_async
        def get_game():
            return Game.objects.select_related("player1", "player2").get(id=self.game_id)
        
        game = await get_game()
        self.scope["game"] = game
        
        # Verificar que el usuario es uno de los jugadores legítimos del juego
        if game and (self.user.id == game.player1.id or self.user.id == game.player2.id):
            # Registrar al usuario como conectado a este juego
            connected_players[self.user.id] = self.channel_name
            await MultiplayerHandler.handle_player_join(self, game)
        else:
            # Usuario no autorizado para este juego
            await self.close(code=4001)

    async def disconnect(self, close_code):
        # Verificar que el canal actual es el que está registrado antes de eliminarlo
        if hasattr(self, 'user') and self.user.id in connected_players and connected_players[self.user.id] == self.channel_name:
            del connected_players[self.user.id]
        
        # Ejecutar la lógica de desconexión
        if self.game_state:
            game = await DatabaseOperations.get_game(self.game_id)
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        message_type = content.get("type")
        if message_type == "move_paddle":
            await GameStateHandler.handle_paddle_movement(self, content)

    async def game_start(self, event):
        if self.game_state:
            await self.game_state.start_countdown()
            asyncio.create_task(GameStateHandler.countdown_timer(self))
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        await self.send(
            text_data=json.dumps({"type": "game_state", "state": event["state"]})
        )
