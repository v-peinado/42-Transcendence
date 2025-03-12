import asyncio
import json
import time
from ..utils.database_operations import DatabaseOperations

class GameStateHandler:
    """Game state updates handler"""

    @staticmethod
    async def handle_paddle_movement(consumer, content):
        """Handle paddle movement"""
        side = content.get("side")
        direction = content.get("direction", 0)
        force_stop = content.get("force_stop", False)
        timestamp = content.get("timestamp", 0)
        player_id = content.get("player_id")
        
        # Validate player has permission for this side
        is_valid_side = False
        try:
            game = consumer.scope.get("game")
            if game:
                if side == "left" and game.player1 and game.player1.id == player_id:
                    is_valid_side = True
                elif side == "right" and game.player2 and game.player2.id == player_id:
                    is_valid_side = True
                    
            if not is_valid_side:
                return
        except Exception:
            pass

        # Store last processed timestamp to prevent processing older messages
        if not hasattr(consumer, "last_movement_timestamp"):
            consumer.last_movement_timestamp = {}

        # Skip outdated messages to prevent "time travel"
        if side in consumer.last_movement_timestamp:
            if timestamp < consumer.last_movement_timestamp[side]:
                return
        
        # Update timestamp
        consumer.last_movement_timestamp[side] = timestamp

        if hasattr(consumer, "game_state") and consumer.game_state:
            paddle = consumer.game_state.paddles.get(side)
            
            # Handle force stop command with complete paddle reset
            if force_stop and direction == 0:
                if paddle and hasattr(paddle, "reset_state"):
                    paddle.reset_state()
                    paddle.moving = False
                    paddle.last_position = paddle.y
                    paddle.target_y = paddle.y
                    paddle.ready_for_input = True
            
            # Ignore command if paddle is not ready for input, unless it's a force stop
            if paddle and not paddle.ready_for_input and not (force_stop and direction == 0):
                return
            
            # During reconnection, ensure pending movements are cleared
            if hasattr(consumer, "reconnecting") and consumer.reconnecting and paddle:
                paddle.moving = direction != 0
                
            # Execute paddle movement in game state
            consumer.game_state.move_paddle(side, direction)

            # Send immediate state update to all clients
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    "type": "game_state_update",
                    "state": consumer.game_state.serialize(),
                },
            )

    @staticmethod
    async def game_loop(consumer):
        """Main game loop"""
        while consumer.game_state.status == "playing":
            winner = consumer.game_state.update(
                asyncio.get_event_loop().time()
            )

            if winner:  # if there's a winner
                game = consumer.scope["game"]
                winner_id = game.player1.id if winner == "left" else game.player2.id
                await DatabaseOperations.update_game_winner(game, winner_id, consumer.game_state)
                await DatabaseOperations.update_game_status(game, "FINISHED")

                await consumer.channel_layer.group_send(
                    consumer.room_group_name,
                    {
                        "type": "game_finished",
                        "winner": winner,
                        "reason": "victory",
                        "final_score": {
                            "left": consumer.game_state.paddles["left"].score,
                            "right": consumer.game_state.paddles["right"].score,
                        },
                    },
                )
                break

            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {"type": "game_state_update", "state": consumer.game_state.serialize()},
            )
            await asyncio.sleep(1/60)  # 60 FPS

    @staticmethod
    async def handle_reconnection_state_sync(consumer):
        """Handle state synchronization for reconnections"""
        if not hasattr(consumer, "game_state") or not consumer.game_state:
            return

        # 1. Get current game state
        current_state = consumer.game_state.serialize()
        
        # 2. Add metadata for fast reconnection
        current_state["fast_reconnect"] = True
        current_state["server_timestamp"] = asyncio.get_event_loop().time() * 1000
        
        # 3. Set player side
        player_side = getattr(consumer, "side", None)
        
        # 4. Send state for fast synchronization
        
        # Send current state
        await consumer.send(text_data=json.dumps({
            "type": "game_state",
            "state": current_state,
            "is_reconnection": True,
            "player_side": player_side,
            "reconnection_sync": True,
            "timestamp": int(time.time() * 1000)
        }))
        
        # Send prediction data immediately to improve experience
        prediction_data = {
            "type": "game_prediction",
            "ball": {
                "x": current_state["ball"]["x"],
                "y": current_state["ball"]["y"],
                "speed_x": current_state["ball"]["speed_x"],
                "speed_y": current_state["ball"]["speed_y"]
            },
            "paddles": {
                "left": {
                    "y": current_state["paddles"]["left"]["y"],
                    "moving": current_state["paddles"]["left"].get("moving", False),
                    "direction": current_state["paddles"]["left"].get("direction", 0)
                },
                "right": {
                    "y": current_state["paddles"]["right"]["y"],
                    "moving": current_state["paddles"]["right"].get("moving", False),
                    "direction": current_state["paddles"]["right"].get("direction", 0)
                }
            },
            "timestamp": int(time.time() * 1000)
        }
        
        # Send prediction data
        await consumer.send(text_data=json.dumps(prediction_data))

    @staticmethod
    async def countdown_timer(consumer):
        """Handle game countdown"""
        consumer.game_state.status = "countdown"
        consumer.game_state.countdown_active = True
        
        # Start countdown
        for countdown_value in [3, 2, 1, "GO!"]:
            consumer.game_state.countdown = countdown_value
            
            # Serialize game state and add sound indicator
            state = consumer.game_state.serialize()
            state["play_sound"] = True
            
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {"type": "game_state_update", "state": state}
            )
            
            # Wait 1 second before next countdown value
            await asyncio.sleep(1)
        
        # Countdown finished, start game
        consumer.game_state.countdown_active = False
        consumer.game_state.countdown = None
        consumer.game_state.status = "playing"

         # Set ball position at game start with correct speed
        consumer.game_state.ball.reset(
            consumer.game_state.CANVAS_WIDTH / 2,
            consumer.game_state.CANVAS_HEIGHT / 2,
            base_speed=consumer.game_state.BALL_SPEED
        )
        
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {
                "type": "game_state_update", 
                "state": consumer.game_state.serialize(),
                "game_started": True
            }
        )

        # Start game loop in background when game starts
        asyncio.create_task(GameStateHandler.game_loop(consumer))
