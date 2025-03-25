from .handlers.multiplayer_handler import MultiplayerHandler
from .handlers.game_state_handler import GameStateHandler
from .utils.database_operations import DatabaseOperations
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .shared_state import game_players
from .base import BaseGameConsumer
import logging
import asyncio
import json
import time

logger = logging.getLogger(__name__) # to log messages in the console

class GameConsumer(BaseGameConsumer):
    async def connect(self):
        """Connect to websocket"""
        try:
            # Use base class connect method
            await super().connect()
            
            # If connection validation failed, return early
            if not hasattr(self, "game_state"):
                return
            
            game = None # Game object
            retry_count = 0	# Retry counter
            
            while not game and retry_count < 3:	# try to get the game 3 times before giving up when connecting
                game = await DatabaseOperations.get_game(self.game_id)	
                if not game:
                    retry_count += 1
                    await asyncio.sleep(0.5)	
            
            if not game:
                logger.error(f"Could not load game {self.game_id} after retries")
                await self.close(code=4004)
                return
                
            self.scope["game"] = game
            
            # Reject connection if game is finished
            if game.status == "FINISHED":
                await self.close(code=4002)
                return
            
            # Verify that the user is authorized to join this game
            if game and (self.user.id == game.player1_id or 
                       (game.player2_id and self.user.id == game.player2_id)):
                # Register the user as connected to this game
                await self.manage_connected_players(add=True)
                await MultiplayerHandler.handle_player_join(self, game)
                
                # Send game information to the client
                player1_info = await self._get_player_info(game.player1_id)
                player2_info = await self._get_player_info(game.player2_id) if game.player2_id else None
                
                await self.send(text_data=json.dumps({
                    "type": "game_info",
                    "player1": player1_info.get('username') if player1_info else 'Unknown',
                    "player2": player2_info.get('username') if player2_info else None,
                    "player1_id": game.player1_id,
                    "player2_id": game.player2_id,
                    "game_id": game.id,
                }))
            else:
                # Unauthorized user, close the connection
                await self.close(code=4001)
            
            # If game is in MATCHED status but countdown not started, initialize countdown
            if game.status == "MATCHED" and self.game_state and not hasattr(self.game_state, "countdown_started"):
                logger.info(f"Game {game.id} is in MATCHED status but countdown not started, initializing")
                self.game_state.countdown_started = False 
            
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            if not hasattr(self, 'websocket_closed'):
                await self.close(code=4500)

    @database_sync_to_async
    def _get_player_info(self, user_id):
        """Get basic player information safely"""
        if not user_id:
            return None
            
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            return {'id': user.id, 'username': user.username}
        except Exception:
            return None

    async def disconnect(self, close_code):
        """Disconnect from websocket"""
        if hasattr(self, "game_state") and self.game_state:
            game = self.scope.get("game")
            if game:
                await MultiplayerHandler.handle_player_disconnect(self)
        await super().disconnect(close_code)
        
        # Update game_players to mark player as disconnected
        if hasattr(self, 'game_id') and hasattr(self, 'side'):
            game_id = str(self.game_id)
            if game_id in game_players and self.side in game_players[game_id]:
                game_players[game_id][self.side]["connected"] = False
                game_players[game_id][self.side]["disconnect_time"] = asyncio.get_event_loop().time()

    async def receive(self, text_data):
        """Receive and process message from websocket"""
        try:
            content = json.loads(text_data)
            message_type = content.get("type")
            
            # Handle ping messages for latency measurement
            if message_type == "ping":
                timestamp = content.get("timestamp")
                await self.send(text_data=json.dumps({
                    "type": "pong",
                    "client_timestamp": timestamp,
                    "server_timestamp": int(time.time() * 1000)
                }))
                return
            
            # Handle paddle movement
            if message_type == "move_paddle":
                await GameStateHandler.handle_paddle_movement(self, content)
            # Handle player ready for countdown con mejoras de robustez
            elif message_type == "ready_for_countdown":
                # We ensure thet we have a game state before setting player ready
                if hasattr(self, "game_state") and self.game_state:
                    self.game_state.player_ready = True
                    
                    # Verify if countdown has started
                    countdown_started = (hasattr(self.game_state, "countdown_started") and 
                                        self.game_state.countdown_started)
                    
                    # If game is not playing and countdown not started, start countdown
                    if not countdown_started and self.game_state.status != "playing":
                        self.game_state.countdown_started = True
                        # Save countdown start time to calculate elapsed time (block countdown)
                        self.game_state.countdown_start_time = time.time()
                        asyncio.create_task(GameStateHandler.countdown_timer(self))
            # Handle chat messages
            elif message_type == "chat_message":
                await self.handle_chat_message(content)
            # Handle reconnect request
            elif message_type == "request_game_state" or message_type == "fast_reconnect":
                await self.send_game_state()
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON from client: {text_data[:100]}")
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
    
    async def handle_chat_message(self, content):
        """Handle chat messages"""
        if not hasattr(self, "user"):
            return
            
        message = content.get("message", "").strip()
        if not message:
            return
            
        # Send message to all in the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.user.username,
                "sender_id": self.user.id,
            }
        )

    async def chat_message(self, event):
        """Send chat message to client"""
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "sender": event["sender"],
            "sender_id": event["sender_id"],
        }))

    async def send_game_state(self):
        """Send the current game state to the client"""
        if hasattr(self, 'game_state') and self.game_state:
            # Identify player side for including in response
            player_side = getattr(self, "side", None)
            
            # If side is not set, try to determine it
            if not player_side:
                game = self.scope.get("game")
                if game:
                    if game.player1_id and self.user.id == game.player1_id:
                        player_side = "left"
                        self.side = "left"
                    elif game.player2_id and self.user.id == game.player2_id:
                        player_side = "right"
                        self.side = "right"
            
            # Restore paddle state for this player if reconnecting
            if player_side and self.game_state.status == 'playing':
                paddle = self.game_state.paddles.get(player_side)
                if paddle:
                    paddle.ready_for_input = True
                    
                    # Restore paddle speed if it was modified
                    paddle.speed = self.game_state.PLAYER_SPEED
                    paddle.original_speed = self.game_state.PLAYER_SPEED
            
            # Send game state to client
            await self.send(text_data=json.dumps({
                "type": "game_state", 
                "state": self.game_state.serialize(),
                "player_side": player_side,
                "is_reconnection": True
            }))

    async def game_start(self, event):
        """Send game start event to client"""
        if hasattr(self, "game_state") and self.game_state:
            await self.game_state.start_countdown()
        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Game loop multiplayer game"""
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        """Send game state update to client"""
        await self.send(text_data=json.dumps({"type": "game_state", "state": event["state"]}))
        
    async def player_disconnected(self, event):
        """Notify the client that a player has disconnected"""
        await self.send(text_data=json.dumps({
            "type": "player_disconnected",
            "side": event["side"],
            "player_id": event["player_id"],
            "username": event.get("username")
        }))
        
    async def player_reconnected(self, event):
        """Notify the client that a player has reconnected"""
        await self.send(text_data=json.dumps({
            "type": "player_reconnected",
            "side": event["side"],
            "player_id": event["player_id"],
            "username": event["username"]
        }))
        
        # If I'm the player who reconnected, send current game state
        if hasattr(self, "side") and self.side == event["side"]:
            await self.send_game_state()
        
    async def game_finished(self, event):
        """Send game finished event to client"""
        await self.send(text_data=json.dumps(event))
