from .handlers.game_state_handler import GameStateHandler
from .handlers.multiplayer_handler import MultiplayerHandler
from .utils.database_operations import DatabaseOperations
from .base import BaseGameConsumer
import asyncio
import json
import time
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .shared_state import game_players

class GameConsumer(BaseGameConsumer):
    async def connect(self):
        """Connect to websocket"""
        try:
            # Use base class connect method
            await super().connect()
            
            # If connection validation failed, return early
            if not hasattr(self, "game_state") or not self.game_state:
                return
            
            # Get game object using database_sync_to_async
            game = await DatabaseOperations.get_game(self.game_id)
            if not game:
                await self.close(code=4004)  # Custom code: Game not found
                return
                
            self.scope["game"] = game
            
            # Reject connection if game is finished
            if game and game.status == "FINISHED":
                await self.close(code=4002)
                return
            
            # Validate player access
            is_valid_player = (game and (self.user.id == game.player1_id or 
                            (game.player2_id is not None and self.user.id == game.player2_id)))
            
            if is_valid_player:
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
                
                # Handle reconnection for in-progress games
                if game.status == "PLAYING" and hasattr(self, "game_state"):
                    side = getattr(self, "side", None)
                    
                    # Set reconnecting flag
                    self.reconnecting = True
                    
                    # Reset paddle state and ensure input is enabled
                    if side:
                        paddle = self.game_state.paddles.get(side)
                        if paddle:
                            current_y = paddle.y
                            paddle.reset_state(current_y)
                            paddle.ready_for_input = True
                    
                    # Send current game state to client
                    player1_name = player1_info.get('username') if player1_info else 'Unknown'
                    player2_name = player2_info.get('username') if player2_info else None
                    
                    await self.send(text_data=json.dumps({
                        "type": "game_state",
                        "state": self.game_state.serialize(),
                        "is_reconnection": True,
                        "player_side": side,
                        "player1": player1_name,
                        "player2": player2_name
                    }))
                    
                    # Short delay before clearing reconnection flag
                    await asyncio.sleep(0.1)
                    self.reconnecting = False
            else:
                # Unauthorized user, close the connection
                await self.close(code=4001)
        except Exception as e:
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
            return {
                'id': user.id,
                'username': user.username
            }
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
        game_id = str(self.game_id)
        if hasattr(self, 'side') and game_id in game_players and self.side in game_players[game_id]:
            game_players[game_id][self.side]["connected"] = False
            game_players[game_id][self.side]["disconnect_time"] = asyncio.get_event_loop().time()
    
    async def determine_player_side(self):
        """Determine which side (left/right) the connected player is on"""
        game = await DatabaseOperations.get_game(self.game_id)
        if not game:
            return None
        
        if game.player1 and game.player1.id == self.user.id:
            return "left"
        elif game.player2 and game.player2.id == self.user.id:
            return "right"
        return None

    async def receive(self, text_data):
        """Receive message from websocket (string)"""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def receive_json(self, content):
        """Receive message from websocket (dictionary)"""
        message_type = content.get("type")
        
        # Handle ping messages for latency measurement
        if message_type == "ping":
            timestamp = content.get("timestamp")
            connection_id = content.get("connectionId")
            await self.send(text_data=json.dumps({
                "type": "pong",
                "client_timestamp": timestamp,
                "server_timestamp": int(time.time() * 1000),
                "connection_id": connection_id
            }))
            return
            
        # Fast reconnect protocol
        if message_type == "fast_reconnect":
            if hasattr(self, "game_state") and self.game_state:
                # Get player side from request
                player_side = content.get("side") or getattr(self, "side", None)
                player_id = content.get("player_id")
                
                # Validate player has permission for this side
                if player_side and player_id and str(player_id) == str(self.user.id):
                    # Set side if not already set
                    if not hasattr(self, "side") or not self.side:
                        self.side = player_side
                    
                    # Reset paddle state without delays
                    paddle = self.game_state.paddles.get(player_side)
                    if paddle:
                        current_y = paddle.y
                        paddle.reset_state(current_y)
                        paddle.ready_for_input = True
                    
                    # Send state immediately with minimal data
                    current_state = {
                        "type": "fast_state",
                        "ball": {
                            "x": self.game_state.ball.x,
                            "y": self.game_state.ball.y,
                            "speed_x": self.game_state.ball.speed_x,
                            "speed_y": self.game_state.ball.speed_y,
                            "radius": self.game_state.ball.radius
                        },
                        "paddles": {
                            "left": {
                                "x": self.game_state.paddles["left"].x,
                                "y": self.game_state.paddles["left"].y,
                                "width": self.game_state.paddles["left"].width,
                                "height": self.game_state.paddles["left"].height,
                                "moving": self.game_state.paddles["left"].moving,
                                "direction": self.game_state.paddles["left"].last_direction,
                            },
                            "right": {
                                "x": self.game_state.paddles["right"].x,
                                "y": self.game_state.paddles["right"].y,
                                "width": self.game_state.paddles["right"].width,
                                "height": self.game_state.paddles["right"].height,
                                "moving": self.game_state.paddles["right"].moving,
                                "direction": self.game_state.paddles["right"].last_direction,
                            }
                        },
                        "score": {
                            "left": self.game_state.paddles["left"].score,
                            "right": self.game_state.paddles["right"].score
                        },
                        "status": self.game_state.status,
                        "player_side": player_side,
                        "timestamp": int(time.time() * 1000)
                    }
                    
                    # Notify that player has reconnected
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "player_reconnected",
                            "side": player_side,
                            "player_id": self.user.id,
                            "username": self.user.username
                        }
                    )
                    
                    # Send fast response
                    await self.send(text_data=json.dumps(current_state))
                    return
        
        if message_type == "move_paddle":
            await GameStateHandler.handle_paddle_movement(self, content)
        elif message_type == "ready_for_countdown":
            # Player is ready for countdown
            if hasattr(self, "game_state") and self.game_state:
                self.game_state.player_ready = True
                if not hasattr(self.game_state, "countdown_started") or not self.game_state.countdown_started:
                    self.game_state.countdown_started = True
                    asyncio.create_task(GameStateHandler.countdown_timer(self))
        elif message_type == "request_game_state":
            # Client is requesting the game state (reconnection)
            if hasattr(self, "game_state") and self.game_state:
                # Set reconnection flag
                self.reconnecting = True
                
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
                
                # Reset paddle state for this player if reconnecting
                if player_side and self.game_state.status == 'playing':
                    paddle = self.game_state.paddles.get(player_side)
                    if paddle:
                        current_y = paddle.y
                        paddle.reset_state(current_y)
                        paddle.ready_for_input = True
                
                # Use specific method for reconnection sync
                await GameStateHandler.handle_reconnection_state_sync(self)
                
                # Clear reconnection flag immediately
                self.reconnecting = False

    async def game_start(self, event):
        """Send game start event to client"""
        if self.game_state:
            await self.game_state.start_countdown()

        await self.send(text_data=json.dumps(event))

    async def game_loop(self):
        """Game loop multiplayer game"""
        await GameStateHandler.game_loop(self)

    async def game_state_update(self, event):
        """Send game state update to client"""
        await self.send(
            text_data=json.dumps({"type": "game_state", "state": event["state"]})
        )
        
    async def player_disconnected(self, event):
        """Notify the client that a player has disconnected"""
        await self.send(
            text_data=json.dumps({
                "type": "player_disconnected",
                "side": event["side"],
                "player_id": event["player_id"]
            })
        )
        
    async def player_reconnected(self, event):
        """Notify the client that a player has reconnected"""
        await self.send(
            text_data=json.dumps({
                "type": "player_reconnected",
                "side": event["side"],
                "player_id": event["player_id"],
                "username": event["username"]
            })
        )
        
    async def game_finished(self, event):
        """Send game finished event to client"""
        await self.send(text_data=json.dumps(event))
        
    async def send_current_game_state(self):
        """Send the current game state to the client"""
        # Check if we have a game state
        if hasattr(self, 'game_state') and self.game_state:
            # Prepare a state update for reconnection
            state_data = self.game_state.serialize()
            
            # Mark this as a reconnection state
            state_data['reconnection'] = True
            
            # Send directly to this client only
            await self.send_json({
                'type': 'game_state',
                'state': state_data
            })
