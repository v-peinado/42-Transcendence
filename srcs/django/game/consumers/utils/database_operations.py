from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from ...models import Game

User = get_user_model()

class DatabaseOperations:
    """Database operations for WebSocket consumers"""
    
    @staticmethod
    @database_sync_to_async
    def create_game(player1, player2):
        """Create a new game with the given players"""
        with transaction.atomic():
            game = Game.objects.create(
                player1=player1,
                player2=player2,
                status='WAITING',
                player1_ready=True,
                player2_ready=True   
            )
            return game

    @staticmethod
    @database_sync_to_async
    def get_game(game_id):
        """Get a game by ID"""
        try:
            # Add .select_related() to preload relationships and avoid async issues
            return Game.objects.select_related('player1', 'player2').get(id=game_id)
        except Game.DoesNotExist:
            return None
        except Exception as e:
            print(f"[DEBUG] Error in get_game: {e}")
            return None

    @staticmethod
    @database_sync_to_async
    def update_game_status(game, status):
        """Update game status"""
        game.status = status
        if status == 'PLAYING' and not game.started_at:
            game.started_at = timezone.now()
        elif status == 'FINISHED' and not game.finished_at:
            game.finished_at = timezone.now()
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def update_game_status_by_id(game_id, status):
        """Update game status by ID"""
        try:
            game = Game.objects.get(id=game_id)
            game.status = status
            if status == 'PLAYING' and not game.started_at:
                game.started_at = timezone.now()
            elif status == 'FINISHED' and not game.finished_at:
                game.finished_at = timezone.now()
            game.save()
            return game
        except Game.DoesNotExist:
            return None
        except Exception as e:
            print(f"[DEBUG] Error in update_game_status_by_id: {e}")
            return None

    @staticmethod
    @database_sync_to_async
    def update_game_scores(game, score1, score2):
        """Update game scores"""
        game.score_player1 = score1
        game.score_player2 = score2
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def update_game_winner(game, winner_id, game_state=None):
        """Update the winner of a game"""
        try:
            winner = User.objects.get(id=winner_id)
            game.winner = winner
            
            # If we have access to the game state, update the scores
            if game_state:
                game.score_player1 = game_state.paddles["left"].score
                game.score_player2 = game_state.paddles["right"].score
                
            game.save()
            return game
        except User.DoesNotExist:
            return None

    @staticmethod
    @database_sync_to_async
    def set_player2(game, player2):
        """Assign a second player to a game"""
        game.player2 = player2
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def mark_player_ready(game, role):
        """Mark a player as ready"""
        if role == "player1":
            game.player1_ready = True
        elif role == "player2":
            game.player2_ready = True
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def update_game_on_disconnect(game, disconnected_side):
        """Update the game when a player disconnects"""
        game.status = "FINISHED"
        game.finished_at = timezone.now()
        
        # Determine the winner by abandonment
        if disconnected_side == "left":
            game.winner = game.player2
        else:
            game.winner = game.player1
            
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def get_player_info(user_id):
        """Get basic player information safely"""
        if not user_id:	# if user id is not provided
            return None
            
        try:
            user = User.objects.get(id=user_id)
            return {'id': user.id, 'username': user.username}
        except Exception:
            return None
