from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
from asgiref.sync import sync_to_async
from ..models import Game

class MatchmakingConsumer(AsyncWebsocketConsumer):
    # Diccionario para mantener la cola de jugadores
    queue = []
    
    async def connect(self):
        await self.channel_layer.group_add(
            'matchmaking',
            self.channel_name
        )
        self.user = self.scope["user"]
        await self.accept()

    async def disconnect(self, close_code):
        # Remover al usuario de la cola si está en ella
        if self.user.id in [player['id'] for player in self.queue]:
            self.queue = [p for p in self.queue if p['id'] != self.user.id]
        
        await self.channel_layer.group_discard(
            'matchmaking',
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'join_queue':
            # Añadir jugador a la cola
            player_info = {
                'id': self.user.id,
                'channel_name': self.channel_name,
                'username': self.user.username
            }
            if player_info not in self.queue:
                self.queue.append(player_info)
                await self.check_for_match()

        elif action == 'leave_queue':
            # Remover jugador de la cola
            self.queue = [p for p in self.queue if p['id'] != self.user.id]

    async def check_for_match(self):
        # Si hay al menos 2 jugadores en la cola
        if len(self.queue) >= 2:
            player1 = self.queue.pop(0)
            player2 = self.queue.pop(0)

            # Crear partida en la base de datos
            game = await self.create_game(player1['id'], player2['id'])

            # Notificar a ambos jugadores
            for player in [player1, player2]:
                await self.channel_layer.send(
                    player['channel_name'],
                    {
                        'type': 'match_found',
                        'game_id': game.id,
                        'player1': player1['username'],
                        'player2': player2['username']
                    }
                )

    async def match_found(self, event):
        # Enviar información de la partida a los clientes
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'game_id': event['game_id'],
            'player1': event['player1'],
            'player2': event['player2']
        }))

    @sync_to_async
    def create_game(self, player1_id, player2_id):
        return Game.objects.create(
            player1_id=player1_id,
            player2_id=player2_id,
            status='WAITING'
        )