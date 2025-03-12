from .base import TranscendenceBaseConsumer
from .shared_state import waiting_players
from .shared_state import connected_players
from .utils.database_operations import DatabaseOperations
import json
import asyncio
import time

class MatchmakingConsumer(TranscendenceBaseConsumer):
    """Consumer for matchmaking"""
    
    async def connect(self):
        """ Validate user connection and add to waiting list """
        if not await self.validate_user_connection():
            return
        
        self.channel = self.channel_name
        
        # Add the user to the waiting list if not already in it
        in_queue = any(item['user'].id == self.user.id for item in waiting_players)
        if not in_queue:
            waiting_players.append({
                'user': self.user, 
                'channel_name': self.channel
            })

        # Register player in connected players
        await self.manage_connected_players(add=True)
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': 'Connected to matchmaking'
        }))
        
        # Try to match players
        await self.try_match_players()

    async def disconnect(self, close_code):
        """ Remove the user from the waiting list """
        # Filter the waiting players list
        self._remove_player_from_queue(self.user.id)
        
        # Remove user from connected players
        await self.manage_connected_players(add=False)

    def _remove_player_from_queue(self, user_id):
        """Helper method to remove a player from the waiting queue"""
        # Create a new list without the specified user
        players_to_keep = []
        for item in waiting_players[:]:  # Create a copy to iterate
            if item['user'].id != user_id:
                players_to_keep.append(item)
        
        # Clear and update the waiting_players list
        waiting_players.clear()
        for player in players_to_keep:
            waiting_players.append(player)

    async def receive_json(self, content):
        """Receive JSON message from client"""
        message_type = content.get('type')
        
        if message_type == 'join_matchmaking':
            # User wants to enter matchmaking
            user = self.scope["user"]
            
            # Check if the user is already in the waiting list before adding
            in_queue = any(item['user'].id == user.id for item in waiting_players)
            if not in_queue:
                # Register player in the waiting list
                waiting_players.append({
                    'user': user,
                    'channel_name': self.channel_name,
                    'join_time': time.time()
                })
                
                # Inform client they are in queue
                await self.send(text_data=json.dumps({
                    'type': 'status',
                    'status': 'waiting',
                    'position': len(waiting_players)
                }))
                
                # Try to match players
                await self.try_match_players()
        
        elif message_type == 'leave_matchmaking':
            # User wants to leave matchmaking
            user_id = self.scope["user"].id
            
            # Remove player from waiting list
            self._remove_player_from_queue(user_id)
            
            # Inform client they have left the queue
            await self.send(text_data=json.dumps({
                'type': 'status',
                'status': 'left_queue'
            }))
        
        elif message_type == 'ping':
            # Reply to ping with pong
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': content.get('timestamp'),
                'server_timestamp': int(time.time() * 1000)
            }))
            
            # Update activity timestamp
            user_id = self.scope["user"].id
            if user_id in connected_players:
                connected_players[user_id]["last_seen"] = time.time()

    async def game_start(self, event):
        """ Send game start event to client """
        await self.send(text_data=json.dumps({
            'type': 'matched',
            'game_id': event['game_id'],
            'player1': event['player1'],
            'player2': event['player2'],
            'player1_id': event['player1_id'],
            'player2_id': event['player2_id'],
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
        if len(waiting_players) >= 2:
            # Get the two first players in the queue
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)

            # Wait until both players are connected
            start_time = time.time()
            timeout = 5  # 5 second timeout
            
            while True:    # Loop until both players are connected
                # Check if both players are still connected
                player1_connected = await self.is_player_connected(player1['user'].id)
                player2_connected = await self.is_player_connected(player2['user'].id)
                
                if player1_connected and player2_connected:    # Both players are connected
                    break    # Exit the loop
                
                if time.time() - start_time > timeout:    # This is to prevent infinite loop
                    # Put the players back in the queue
                    if player1_connected:
                        waiting_players.append(player1)
                    if player2_connected:
                        waiting_players.append(player2)
                    return
                
                await asyncio.sleep(0.1)

            # Create new game
            game = await DatabaseOperations.create_game(player1['user'], player2['user'])

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
            # Inform client about their position in the queue
            position = next((i+1 for i, p in enumerate(waiting_players) if p['user'].id == self.user.id), 0)
            await self.send(text_data=json.dumps({
                'type': 'status',
                'status': 'waiting',
                'position': position
            }))
    
    async def is_player_connected(self, player_id):
        """Check if a player is still connected to the matchmaking system"""
        return player_id in connected_players

    async def receive(self, text_data):
        """Receive message from WebSocket in text format and convert to JSON"""
        try:
            data = json.loads(text_data)
            await self.receive_json(data)
        except json.JSONDecodeError:
            # Send error message to client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))