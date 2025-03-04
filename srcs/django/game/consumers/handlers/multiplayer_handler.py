import asyncio
from channels.db import database_sync_to_async
from django.db import transaction
from game.models import Game


class MultiplayerHandler:
    """Handles multiplayer game logic"""

    @staticmethod
    async def handle_player_join(consumer, game):
        """Assign player to game and mark player as ready"""
        if game.player1 == consumer.user:
            consumer.side = "left"
            await MultiplayerHandler.mark_player_ready(game, role="player1")
        else:
            consumer.side = "right"
            if game.player2 != consumer.user:
                await MultiplayerHandler.set_player2(game, consumer.user)
            await MultiplayerHandler.mark_player_ready(game, role="player2")

        updated_game = await MultiplayerHandler.get_game(game.id)
        if (updated_game.player1_ready and updated_game.player2_ready) and (updated_game.status != "PLAYING"):
            updated_game = await MultiplayerHandler.update_game_status(updated_game, "PLAYING")

            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    "type": "game_start",
                    "player1": updated_game.player1.username,
                    "player2": updated_game.player2.username,
                    "player1_id": updated_game.player1.id,
                    "player2_id": updated_game.player2.id,
                    "game_id": updated_game.id,
                },
            )
            # Start game countdown
            consumer.game_state.status = "countdown"
            await consumer.game_state.start_countdown()
            asyncio.create_task(consumer.game_loop())
            
    @staticmethod
    async def handle_player_disconnect(consumer):
        """Handle player disconnection (desertion)"""
        if consumer.game_state.status == "finished":
            return
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
            
    @staticmethod
    @database_sync_to_async
    def mark_player_ready(game, role):
        if role == "player1":
            game.player1_ready = True
        elif role == "player2":
            game.player2_ready = True
        game.save()

    @staticmethod
    @database_sync_to_async
    def set_player2(game, user):
        if game.player2 != user:
            game.player2 = user
            game.save()

    @staticmethod
    @database_sync_to_async
    def update_game_status(game, status):
        game.status = status
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def get_game(game_id):
        return Game.objects.select_related("player1", "player2").get(id=game_id)
