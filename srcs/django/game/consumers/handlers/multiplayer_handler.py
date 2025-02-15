import asyncio
from channels.db import database_sync_to_async
from django.db import transaction


class MultiplayerHandler:
    """Handles multiplayer game logic"""

    @staticmethod
    async def handle_player_join(consumer, game):
        """Start or join multiplayer game"""
        if game.status != "MATCHED":  # When trying to join after game has started
            raise ValueError("Cannot join a game that has already started")

        player1 = await database_sync_to_async(getattr)(
            game, "player1"
        )  # Player 1 is the game creator

        if player1 == consumer.user:  # If current user is player 1
            consumer.side = "left"
        else:  # If current user is player 2
            consumer.side = "right"

            @database_sync_to_async
            def update_game():
                with transaction.atomic():  # Operation is atomic (all or nothing)
                    game.refresh_from_db()  # Refresh game from database
                    game.player2 = consumer.user  # Set player 2 as current user
                    game.status = "PLAYING"  # Set game status to 'PLAYING'
                    game.save()  # Save game to database
                return game  # Return updated game

            await update_game()

            # Notify both players about game start
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    "type": "game_start",
                    "player1": player1.username,
                    "player2": consumer.user.username,
                    "player1_id": player1.id,
                    "player2_id": consumer.user.id,
                },
            )

            consumer.game_state.status = "countdown"
            await consumer.game_state.start_countdown()
            asyncio.create_task(consumer.game_loop())

    @staticmethod
    async def handle_player_disconnect(consumer):
        """Handle player disconnection (desertion)"""
        if hasattr(consumer, "side"):
            winner_side = (
                "right" if consumer.side == "left" else "left"
            )  # If left player disconnects, right wins and vice versa
            consumer.game_state.status = "finished"

            @database_sync_to_async
            def update_game_on_disconnect():  # Update game when a player disconnects
                with transaction.atomic():
                    game = consumer.scope["game"]
                    game.refresh_from_db()
                    game.status = "FINISHED"
                    if consumer.side == "left":
                        game.winner = game.player2
                    else:
                        game.winner = game.player1
                    game.save()
                return game

            await update_game_on_disconnect()

            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    "type": "game_finished",
                    "winner": winner_side,
                    "reason": "desertion",  # Specify game ended due to player desertion
                    "deserter": consumer.side,
                    "final_score": {
                        "left": consumer.game_state.paddles["left"].score,
                        "right": consumer.game_state.paddles["right"].score,
                    },
                },
            )
