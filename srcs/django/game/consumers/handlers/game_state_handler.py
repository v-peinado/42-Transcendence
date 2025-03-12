import asyncio
import json
import time
from ..utils.database_operations import DatabaseOperations

class GameStateHandler:
    """Game state updates handler"""

    @staticmethod
    async def handle_paddle_movement(consumer, content):
        """Handle paddle movement"""
        side = content.get("side")  # Player's side
        direction = content.get("direction", 0)  # Paddle movement direction (0 = still, 1 = up, -1 = down)
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

        if hasattr(consumer, "game_state") and consumer.game_state:
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
