from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from ...models import Game


class DatabaseOperations:
    """Asynchronous database operations"""

    @staticmethod
    @database_sync_to_async
    def get_game(game_id):
        """Get game by ID"""
        try:
            return Game.objects.select_related("player1", "player2").get(id=game_id)
        except Game.DoesNotExist:
            return None

    @staticmethod
    @database_sync_to_async
    def get_player1(game):
        """Get player 1 from game"""
        return game.player1

    @staticmethod
    @database_sync_to_async
    def get_player2(game):
        """Get player 2 from game"""
        return game.player2

    @staticmethod
    @database_sync_to_async
    def update_game(game, user):
        """Update game when second player joins"""
        game.player2 = user
        game.status = "PLAYING"
        game.save()

    @staticmethod
    @database_sync_to_async
    def update_game_status(game, status):
        """Update game status"""
        with transaction.atomic():
            game.refresh_from_db()
            game.status = status
            if status == "FINISHED":
                game.finished_at = timezone.now()
            game.save()

    @staticmethod
    @database_sync_to_async
    def update_game_winner(game, winner_id, game_state):
        """Update game winner"""
        with transaction.atomic():
            game.refresh_from_db()
            game.winner_id = winner_id
            game.score_player1 = game_state.paddles["left"].score
            game.score_player2 = game_state.paddles["right"].score
            game.save()
