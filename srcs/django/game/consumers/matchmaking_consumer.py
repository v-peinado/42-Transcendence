import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Game
from django.contrib.auth import get_user_model
import asyncio
from .shared_state import connected_players, waiting_players
import time

User = get_user_model()

class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.channel = self.channel_name
        
        # Verificar si el usuario ya está conectado desde otro navegador
        if self.user.id in connected_players:
            existing_channel = connected_players[self.user.id]
            if existing_channel != self.channel_name:
                # Usuario ya conectado desde otro lugar, rechazar la conexión
                await self.close(code=4000)  # Código personalizado para indicar "ya conectado"
                return
                
        # Agregar el usuario a la lista de espera si no está ya
        in_queue = any(item['user'].id == self.user.id for item in waiting_players)
        if not in_queue:
            waiting_players.append({'user': self.user, 'channel_name': self.channel})

        # Agregar el usuario a la lista de conectados
        connected_players[self.user.id] = self.channel_name

        await self.accept()
        await self.try_match_players()

    async def disconnect(self, close_code):
        global waiting_players, connected_players
        # Eliminar al usuario de la lista de espera
        waiting_players = [item for item in waiting_players if item['user'].id != self.user.id]
        
        # Verificar que el canal actual es el que está registrado antes de eliminarlo
        if self.user.id in connected_players and connected_players[self.user.id] == self.channel_name:
            del connected_players[self.user.id]

    async def game_start(self, event):
        await self.send(text_data=json.dumps({
            'game_id': event['game_id'],
            'status': 'matched'
        }))
        
    async def game_state_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state_update',
            'state': event['state']
        }))

    async def try_match_players(self):
        global waiting_players, connected_players
        if len(waiting_players) >= 2:
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)

            # Espera hasta que ambos jugadores estén conectados
            start_time = time.time()
            while (player1['user'].id not in connected_players or
                    player2['user'].id not in connected_players):
                if time.time() - start_time > 5:  # Timeout de 5 segundos
                    # Volver a poner a los jugadores en la cola
                    waiting_players.append(player1)
                    waiting_players.append(player2)
                    return
                await asyncio.sleep(0.1)

            game = await self.create_game(player1['user'], player2['user'])
            print(f"Match found between {player1['user']} and {player2['user']} for game {game.id}")

            # Agregar ambos canales al grupo del juego
            await self.channel_layer.group_add(f'game_{game.id}', player1['channel_name'])
            await self.channel_layer.group_add(f'game_{game.id}', player2['channel_name'])

            # Notificar a ambos que se ha hecho el match (aquí los clientes cargarán la vista de juego)
            await self.channel_layer.group_send(
                f'game_{game.id}',
                {
                    'type': 'game_start',
                    'game_id': game.id
                }
            )

            # Actualizar el estado del juego a MATCHED
            await self.update_game_status(game.id, 'MATCHED')
        else:
            await self.send(text_data=json.dumps({
                'status': 'waiting'
            }))
            print(f"User {self.user} is waiting for another player.")

    @database_sync_to_async
    def create_game(self, player1, player2):
        # Se crea inicialmente en WAITING y luego se actualiza a MATCHED
        return Game.objects.create(player1=player1, player2=player2, status='WAITING')

    @database_sync_to_async
    def update_game_status(self, game_id, status):
        game = Game.objects.get(id=game_id)
        game.status = status
        game.save()