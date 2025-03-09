from .base import TranscendenceBaseConsumer
from .shared_state import waiting_players
from .utils.database_operations import DatabaseOperations
import asyncio
import json
import time

class MatchmakingConsumer(TranscendenceBaseConsumer):
    async def connect(self):
        """ Validate user connection and add to waiting list """
        if not await self.validate_user_connection():
            return
        
        self.channel = self.channel_name
        
        # Add the user to the waiting list if not already in it
        in_queue = any(item['user'].id == self.user.id for item in waiting_players)
        if not in_queue:
            waiting_players.append({'user': self.user, 'channel_name': self.channel})

        # If the user is already connected, remove the old connection 
		# from the connected_players dictionary and add the new one
        await self.manage_connected_players(add=True)

        await self.accept()
        await self.try_match_players()

    async def disconnect(self, close_code):
        """ Remove the user from the waiting list """
        global waiting_players
        waiting_players = [item for item in waiting_players if item['user'].id != self.user.id]
        
        # Remove user from connected players
        await self.manage_connected_players(add=False)

    async def game_start(self, event):
        """ Send game start event to client """
        await self.send(text_data=json.dumps({
            'game_id': event['game_id'],
            'status': 'matched'
        }))
        
    async def game_state_update(self, event):
        """ Send game state update to client """
        await self.send(text_data=json.dumps({
            'type': 'game_state_update',
            'state': event['state']
        }))

    async def try_match_players(self):
        """ Try to match two players from the waiting list """
        global waiting_players
        if len(waiting_players) >= 2:
            player1 = waiting_players.pop(0)	# Remove player1 from the queue...
            player2 = waiting_players.pop(0)	# Remove player2 from the queue...

            # Wait until both players are connected
            start_time = time.time()
            timeout = 5  # 5 second timeout
            
            while True:	# Loop until both players are connected
                
				# Check if both players are still connected
                player1_connected = await self.is_player_connected(player1['user'].id)
                player2_connected = await self.is_player_connected(player2['user'].id)
                
                if player1_connected and player2_connected:	# Both players are connected
                    break	# Exit the loop
                
                if time.time() - start_time > timeout:	# This is to prevent infinite loop
                    # Put the players back in the queue
                    if player1_connected:
                        waiting_players.append(player1)
                    if player2_connected:
                        waiting_players.append(player2)
                    return
                
                await asyncio.sleep(0.1)

            game = await DatabaseOperations.create_game(player1['user'], player2['user'])
            # print(f"Match found between {player1['user']} and {player2['user']} for game {game.id}")

            # Add both channels to the game group
            await self.channel_layer.group_add(f'game_{game.id}', player1['channel_name'])
            await self.channel_layer.group_add(f'game_{game.id}', player2['channel_name'])

            # Notify both that the match has been made
            await self.channel_layer.group_send(
                f'game_{game.id}',
                {
                    'type': 'game_start',
                    'player1': player1['user'].username,
                    'player2': player2['user'].username,
                    'player1_id': player1['user'].id,
                    'player2_id': player2['user'].id,
                    'game_id': game.id
                }
            )

            # Update the game status to MATCHED
            await DatabaseOperations.update_game_status_by_id(game.id, 'MATCHED')
        else:
            await self.send(text_data=json.dumps({
                'status': 'waiting'
            }))
            #print(f"User {self.user} is waiting for another player.")
    
    async def is_player_connected(self, player_id):
        """Check if a player is still connected to the matchmaking system"""
        from .shared_state import connected_players
        return player_id in connected_players