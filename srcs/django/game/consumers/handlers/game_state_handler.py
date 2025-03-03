import asyncio
from channels.db import database_sync_to_async
from django.db import transaction

class GameStateHandler:
    """Game state updates handler"""

    @staticmethod
    async def handle_paddle_movement(consumer, content):
        """Handle paddle movement"""
        side = content.get("side")  # Player's side
        direction = content.get(
            "direction", 0
        )  # Paddle movement direction (0 = still, 1 = up, -1 = down)

        if (
            hasattr(consumer, "game_state") and consumer.game_state
        ):  # Check if there's an active game and game state
            consumer.game_state.move_paddle(side, direction)  # Move paddle

            await consumer.channel_layer.group_send(  # Send game state update message
                consumer.room_group_name,
                {
                    "type": "game_state_update",  # Define message type as 'game_state_update'
                    "state": consumer.game_state.serialize(),  # Serialize and send game state
                },
            )

    @staticmethod
    async def game_loop(consumer):  # Main game loop
        """Main game loop"""
        while consumer.game_state.status == "playing":
            winner = consumer.game_state.update(
                asyncio.get_event_loop().time()
            )  # Update game state and check for winner

            if winner:  # If there's a winner

                @database_sync_to_async  # Update game winner in database
                def update_game_winner():
                    with transaction.atomic():  # Ensure operation is atomic (all or nothing)
                        game = consumer.scope["game"]  # Get current game
                        game.refresh_from_db()  # Refresh game object from database
                        game.status = "FINISHED"  # Set game status to 'FINISHED'
                        if winner == "left":  # If left player wins
                            game.winner = game.player1
                            game.score_player1 = consumer.game_state.paddles[
                                "left"
                            ].score
                            game.score_player2 = consumer.game_state.paddles[
                                "right"
                            ].score
                        else:  # If right player wins
                            game.winner = game.player2
                            game.score_player1 = consumer.game_state.paddles[
                                "left"
                            ].score
                            game.score_player2 = consumer.game_state.paddles[
                                "right"
                            ].score
                        game.save()

                await update_game_winner()  # Wait for game winner update

                await consumer.channel_layer.group_send(  # Send game finished message
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
                break  # Exit loop if there's a winner

            await consumer.channel_layer.group_send(  # Send game state update to other player
                consumer.room_group_name,
                {"type": "game_state_update", "state": consumer.game_state.serialize()},
            )
            await asyncio.sleep(
                1 / 60
            )  # Wait 1/60 seconds before next iteration (60 FPS)

    @staticmethod
    async def countdown_timer(consumer):  # Countdown timer
        """Handle game countdown"""
        countdown_value = 3

        while countdown_value > 0:
            consumer.game_state.countdown = countdown_value  # Update countdown value
            state = consumer.game_state.serialize()  # Serialize game state

            await consumer.channel_layer.group_send(  # Send game state update
                consumer.room_group_name, {"type": "game_state_update", "state": state}
            )

            await asyncio.sleep(1)  # Display numbers each second
            countdown_value -= 1  # Decrement countdown value

        # Start game after countdown
        consumer.game_state.countdown_active = False
        consumer.game_state.countdown = 0
        consumer.game_state.status = "playing"

        # Set ball position at game start
        consumer.game_state.ball.reset(
            consumer.game_state.CANVAS_WIDTH / 2, consumer.game_state.CANVAS_HEIGHT / 2
        )

        # Send updated game state when game starts
        await consumer.channel_layer.group_send(
            consumer.room_group_name,
            {"type": "game_state_update", "state": consumer.game_state.serialize()},
        )

        # Start game loop
        asyncio.create_task(GameStateHandler.game_loop(consumer))
