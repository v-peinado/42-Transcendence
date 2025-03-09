from ..utils.database_operations import DatabaseOperations
import asyncio

class MultiplayerHandler:
    """Handles multiplayer game logic"""
    
    @staticmethod
    async def handle_player_join(consumer, game):
        """Assign player to game side and mark player as ready"""
        if game.player1 == consumer.user:
            consumer.side = "left"
            await DatabaseOperations.mark_player_ready(game, role="player1")
        else:
            consumer.side = "right"
            if game.player2 != consumer.user:
                await DatabaseOperations.set_player2(game, consumer.user)
            await DatabaseOperations.mark_player_ready(game, role="player2")

        updated_game = await DatabaseOperations.get_game(game.id)
        if (updated_game.player1_ready and updated_game.player2_ready) and (updated_game.status != "PLAYING"):
            updated_game = await DatabaseOperations.update_game_status(updated_game, "PLAYING")

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
            winner_side = "right" if consumer.side == "left" else "left"
            consumer.game_state.status = "finished"

            game = consumer.scope["game"]
            await DatabaseOperations.update_game_on_disconnect(game, consumer.side)

            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    "type": "game_finished",
                    "winner": winner_side,
                    "reason": "desertion",
                    "deserter": consumer.side,
                    "final_score": {
                        "left": consumer.game_state.paddles["left"].score,
                        "right": consumer.game_state.paddles["right"].score,
                    },
                },
            )
