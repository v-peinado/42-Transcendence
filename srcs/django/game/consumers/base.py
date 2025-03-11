from channels.generic.websocket import AsyncWebsocketConsumer
import json
from ..engine.game_state import GameState
from .utils.diagnostic import DiagnosticLogger as diag
from .shared_state import connected_players

class TranscendenceBaseConsumer(AsyncWebsocketConsumer):
    """Base consumer with common functionality"""
    
    async def validate_user_connection(self):
        """Validate user authentication and connection"""
        try:
            # Check if user is authenticated
            if not self.scope["user"].is_authenticated:
                await self.close(code=4001)  # Unauthorized
                diag.warn('BaseConsumer', 'Connection attempt by unauthenticated user')
                return False
            
            # Store user reference for convenience
            self.user = self.scope["user"]
            return True
        except Exception as e:
            diag.error('BaseConsumer', f'Error validating user connection: {e}')
            await self.close(code=4500)  # Internal error
            return False
    
    async def manage_connected_players(self, add=True):
        """Add/remove user from connected players"""
        try:
            user_id = self.user.id
            
            if add:
                connected_players[user_id] = {
                    "channel_name": self.channel_name,
                    "username": self.user.username,
                    "last_seen": 0
                }
                diag.info('BaseConsumer', f'Added user {self.user.username} to connected players')
            else:
                if user_id in connected_players:
                    del connected_players[user_id]
                    diag.info('BaseConsumer', f'Removed user {self.user.username} from connected players')
        except Exception as e:
            diag.error('BaseConsumer', f'Error managing connected players: {e}')

    async def game_state_update(self, event):
        """Send game state update to client"""
        await self.send(text_data=json.dumps({
            "type": "game_state", 
            "state": event["state"]
        }))
    
    async def game_start(self, event):
        """Send game start event to client"""
        await self.send(text_data=json.dumps(event))
    
    async def game_finished(self, event):
        """Send game finished event to client"""
        await self.send(text_data=json.dumps(event))


class BaseGameConsumer(TranscendenceBaseConsumer):
    """Base consumer for game connections"""
    
    async def connect(self):
        """Connect to websocket"""
        try:
            # Check authentication using the base class method
            if not await self.validate_user_connection():
                return
            
            # Parse game_id from URL route
            self.game_id = self.scope['url_route']['kwargs']['game_id']
            self.room_group_name = f'game_{self.game_id}'
            
            # Join game group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Create game state if not exists
            if not hasattr(self, "game_state"):
                from .shared_state import game_players, game_states
                game_id = str(self.game_id)
                
                # Check if there's an existing game state in our shared dictionary
                if game_id in game_states:
                    self.game_state = game_states[game_id]
                    diag.info('BaseGameConsumer', f'Reusing existing game state from shared memory for game {self.game_id}')
                # If no existing game state, create a new one
                else:
                    self.game_state = GameState()
                    # Store in shared dictionary for other connections to use
                    game_states[game_id] = self.game_state
                    diag.info('BaseGameConsumer', f'Created new game state for game {self.game_id}')
            
            await self.accept()
            
        except Exception as e:
            diag.error('BaseGameConsumer', f'Error in connect: {e}')
            if hasattr(self, 'websocket') and not self.websocket.closed:
                await self.close(code=4500)
    
    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
