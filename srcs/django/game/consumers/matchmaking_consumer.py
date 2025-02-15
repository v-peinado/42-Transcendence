import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ..models import Game
from django.contrib.auth import get_user_model
import asyncio

User = get_user_model()

waiting_players = []
connected_players = {}

class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.channel = self.channel_name

        # Add user + channel_name to waiting list if not there already
        in_queue = any(item['user'] == self.user for item in waiting_players)
        if not in_queue:
            waiting_players.append({'user': self.user, 'channel_name': self.channel})

        # Add user to connected players
        connected_players[self.user.id] = self.channel_name

        await self.accept()
        await self.try_match_players()

    async def disconnect(self, close_code):
        global waiting_players, connected_players
        waiting_players = [
            item for item in waiting_players
            if item['user'] != self.user
        ]
        if self.user.id in connected_players:
            del connected_players[self.user.id]

    async def game_start(self, event):
        await self.send(text_data=json.dumps({
            'game_id': event['game_id'],
            'status': 'matched'
        }))

    async def try_match_players(self):
        """
        If at least two players are waiting, create a game and add both
        channel_names to the same group, then send 'matched' to both.
        """
        global waiting_players, connected_players
        if len(waiting_players) >= 2:
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)

            # Wait until both players are connected
            while player1['user'].id not in connected_players or player2['user'].id not in connected_players:
                await asyncio.sleep(0.1)

            game = await self.create_game(player1['user'], player2['user'])
            print(f"Match found between {player1['user']} and {player2['user']} for game {game.id}")

            # Add both channels to game group
            await self.channel_layer.group_add(f'game_{game.id}', player1['channel_name'])
            await self.channel_layer.group_add(f'game_{game.id}', player2['channel_name'])

            # Notify group of game start
            await self.channel_layer.group_send(
                f'game_{game.id}',
                {
                    'type': 'game_start',
                    'game_id': game.id
                }
            )

            # Update game status to 'MATCHED'
            await self.update_game_status(game.id, 'MATCHED')
        else:
            # If not matched yet, let this consumer know to wait
            await self.send(text_data=json.dumps({
                'status': 'waiting'
            }))
            print(f"User {self.user} is waiting for another player.")

    @database_sync_to_async
    def create_game(self, player1, player2):
        return Game.objects.create(player1=player1, player2=player2, status='WAITING')

    @database_sync_to_async
    def update_game_status(self, game_id, status):
        game = Game.objects.get(id=game_id)
        game.status = status
        game.save()