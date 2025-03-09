from channels.generic.websocket import AsyncWebsocketConsumer
from .shared_state import connected_players, waiting_players
from .utils.database_operations import DatabaseOperations
from django.contrib.auth import get_user_model
import asyncio
import json
import time

User = get_user_model()

class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.channel = self.channel_name
        
        # Check if the user is already connected from another browser
        if self.user.id in connected_players:
            existing_channel = connected_players[self.user.id]
            if existing_channel != self.channel_name:
                # User already connected from another location, reject the connection
                await self.close(code=4000)  # Código personalizado para indicar "ya conectado"
                return
                
        # Add the user to the waiting list if not already there
        in_queue = any(item['user'].id == self.user.id for item in waiting_players)
        if not in_queue:
            waiting_players.append({'user': self.user, 'channel_name': self.channel})

        # Add the user to the connected list
        connected_players[self.user.id] = self.channel_name

        await self.accept()
        await self.try_match_players()

    async def disconnect(self, close_code):
        global waiting_players, connected_players
        # Remove the user from the waiting list
        waiting_players = [item for item in waiting_players if item['user'].id != self.user.id]
        
        # Verify that the current channel is the one registered before removing it
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

            # Wait until both players are connected
            start_time = time.time()
            while (player1['user'].id not in connected_players or
                    player2['user'].id not in connected_players):
                if time.time() - start_time > 5:  # 5 second timeout
                    # Put the players back in the queue
                    waiting_players.append(player1)
                    waiting_players.append(player2)
                    return
                await asyncio.sleep(0.1)

            game = await DatabaseOperations.create_game(player1['user'], player2['user'])
            print(f"Match found between {player1['user']} and {player2['user']} for game {game.id}")

            # Add both channels to the game group
            await self.channel_layer.group_add(f'game_{game.id}', player1['channel_name'])
            await self.channel_layer.group_add(f'game_{game.id}', player2['channel_name'])

            # Notify both that the match has been made (here clients will load the game view)
            await self.channel_layer.group_send(
                f'game_{game.id}',
                {
                    'type': 'game_start',
                    'game_id': game.id
                }
            )

            # Update the game status to MATCHED
            await DatabaseOperations.update_game_status_by_id(game.id, 'MATCHED')
        else:
            await self.send(text_data=json.dumps({
                'status': 'waiting'
            }))
            print(f"User {self.user} is waiting for another player.")