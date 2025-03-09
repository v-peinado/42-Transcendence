from channels.generic.websocket import AsyncWebsocketConsumer
from ..engine.game_state import GameState
from .shared_state import connected_players
import json

class TranscendenceBaseConsumer(AsyncWebsocketConsumer):
    """Base consumer with common functionality for all Pong game consumers"""
    
    async def validate_user_connection(self):
        """Validate if user is already connected from another location"""
        self.user = self.scope["user"]
        
        # Verify that the user is connected from only one place
        if self.user.id in connected_players:
            existing_channel = connected_players[self.user.id]
            if existing_channel != self.channel_name:
                # User is already connected from another place, reject this connection
                await self.close(code=4000)
                return False	# connection rejected
        
        return True	# connection accepted
        
    async def manage_connected_players(self, add=True):
        """Add or remove user from connected_players dictionary"""
        if add:
            connected_players[self.user.id] = self.channel_name
        else:
            # Verify that the user is connected to this channel before disconnecting
            if hasattr(self, "user") and self.user.id in connected_players and connected_players[self.user.id] == self.channel_name:
                del connected_players[self.user.id]
    
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
    """Base game consumer with game-specific functionality"""
    
    game_states = {}    # Storing game states (game_id: GameState object)

    async def connect(self):
        """Connect to websocket"""
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = f"game_{self.game_id}"
        
        # Validate user connection using base consumer method
        if not await self.validate_user_connection():
            return
            
        self.game_state = await self.initialize_game_state()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        # Remove user from connected players
        await self.manage_connected_players(add=False)
        
        if hasattr(self, "game_id") and self.game_id in self.game_states:
            del self.game_states[self.game_id]

        if hasattr(self, "room_group_name") and hasattr(self, "channel_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def initialize_game_state(self):
        """Game state initialization"""
        if self.game_id not in self.game_states:
            self.game_states[self.game_id] = GameState()
        return self.game_states[self.game_id]
