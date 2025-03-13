from channels.generic.websocket import AsyncWebsocketConsumer
from .shared_state import game_states, connected_players
from ..engine.game_state import GameState
import json

class TranscendenceBaseConsumer(AsyncWebsocketConsumer):
    """Base consumer with common functionality for all Pong game consumers"""
    
    async def validate_user_connection(self):
        """Validate if user is already connected from another location"""
        try:
            if not self.scope["user"].is_authenticated: # if user is not authenticated
                await self.close(code=4001)  # Unauthorized
                return False
            
            self.user = self.scope["user"] # get user object
            return True
        except Exception:
            await self.close(code=4500)  # Internal error
            return False
    
    async def manage_connected_players(self, add=True):
        """Add or remove user from connected_players dictionary"""
        try:
            user_id = self.user.id	# get user id
            
            if add:	# if user is connecting
                connected_players[user_id] = {
                    "channel_name": self.channel_name,
                    "username": self.user.username,
                    "last_seen": 0
                }
            else:	# if user is disconnecting
                if user_id in connected_players:
                    del connected_players[user_id]
        except Exception:	# if any error occurs
            pass	# do nothing

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
    
    async def connect(self):
        """Connect to websocket and add to game group"""
        try:
            if not await self.validate_user_connection(): # if user is not authenticated
                return
            
            self.game_id = self.scope['url_route']['kwargs']['game_id'] # get game id
            self.room_group_name = f'game_{self.game_id}'	# create room group name
            
            await self.channel_layer.group_add(	# add user to the room group
                self.room_group_name,
                self.channel_name
            )
            
            if not hasattr(self, "game_state"):	# if game state is not already set
                game_id = str(self.game_id)	# get game id as string
                
                if game_id in game_states:	# if game state is already set
                    self.game_state = game_states[game_id]	# get game state
                else:	# if game state is not set
                    self.game_state = GameState()	# create new game state
                    game_states[game_id] = self.game_state	# set game state
            
            await self.accept()
            
        except Exception:
            if hasattr(self, 'websocket') and not self.websocket.closed:
                await self.close(code=4500)
    
    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
