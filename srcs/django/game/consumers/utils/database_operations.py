from channels.db import database_sync_to_async
from django.db import transaction
from ...models import Game


class DatabaseOperations:
    """Asynchronous database operations"""

# Getters

    @staticmethod
    @database_sync_to_async
    def create_game(player1, player2):
        """Create a new game"""
        return Game.objects.create(player1=player1, player2=player2, status='WAITING')
    
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
    

# Setters

    @staticmethod
    @database_sync_to_async
    def mark_player_ready(game, role):
        """Mark player as ready"""
        if role == "player1":
            game.player1_ready = True
        elif role == "player2":
            game.player2_ready = True
        game.save()
        
    @staticmethod
    @database_sync_to_async
    def set_player2(game, user):
        """Set player 2 for a game"""
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
    def update_game(game, user):
        """Update game when second player joins"""
        game.player2 = user
        game.status = "PLAYING"
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
            

    @staticmethod
    @database_sync_to_async
    def update_game_status_by_id(game_id, status):
        """Update game status by ID"""
        game = Game.objects.get(id=game_id)
        game.status = status
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def update_game_on_disconnect(game, side):
        """Update game when a player disconnects"""
        with transaction.atomic():
            game.refresh_from_db()
            game.status = "FINISHED"
            if side == "left":
                game.winner = game.player2
            else:
                game.winner = game.player1
            game.save()
            return game
