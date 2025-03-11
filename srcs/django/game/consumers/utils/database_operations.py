from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from ...models import Game
from channels.db import database_sync_to_async

User = get_user_model()

class DatabaseOperations:
    """Operaciones de base de datos para consumidores WebSocket"""
    
    @staticmethod
    @database_sync_to_async
    def create_game(player1, player2=None):
        """Crear un nuevo juego con los jugadores dados"""
        with transaction.atomic():
            game = Game.objects.create(
                player1=player1,
                player2=player2,
                status='WAITING'
            )
            return game

    @staticmethod
    @database_sync_to_async
    def get_game(game_id):
        """Obtener un juego por ID"""
        try:
            # Añadir .select_related() para precargar relaciones y evitar problemas con async
            return Game.objects.select_related('player1', 'player2').get(id=game_id)
        except Game.DoesNotExist:
            return None
        except Exception as e:
            print(f"[DEBUG] Error en get_game: {e}")
            return None

    @staticmethod
    @database_sync_to_async
    def update_game_status(game, status):
        """Actualizar el estado de un juego"""
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
        """Actualizar el estado de un juego por ID"""
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
            print(f"[DEBUG] Error en update_game_status_by_id: {e}")
            return None

    @staticmethod
    @database_sync_to_async
    def update_game_scores(game, score1, score2):
        """Actualizar las puntuaciones del juego"""
        game.score_player1 = score1
        game.score_player2 = score2
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def update_game_winner(game, winner_id, game_state=None):
        """Actualizar el ganador de un juego"""
        try:
            winner = User.objects.get(id=winner_id)
            game.winner = winner
            
            # Si tenemos acceso al estado del juego, actualizamos las puntuaciones
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
        """Asignar un segundo jugador a un juego"""
        game.player2 = player2
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def mark_player_ready(game, role):
        """Marcar a un jugador como listo"""
        if role == "player1":
            game.player1_ready = True
        elif role == "player2":
            game.player2_ready = True
        game.save()
        return game

    @staticmethod
    @database_sync_to_async
    def update_game_on_disconnect(game, disconnected_side):
        """Actualizar el juego cuando un jugador se desconecta"""
        game.status = "FINISHED"
        game.finished_at = timezone.now()
        
        # Determinar al ganador por abandono
        if disconnected_side == "left":
            game.winner = game.player2
        else:
            game.winner = game.player1
            
        game.save()
        return game
