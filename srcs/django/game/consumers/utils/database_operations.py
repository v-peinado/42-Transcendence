from channels.db import database_sync_to_async
from ...models import Game

class DatabaseOperations:
    """Operaciones de base de datos asíncronas"""

    @staticmethod
    @database_sync_to_async
    def get_game(game_id):
        """Obtener juego por ID"""
        try:
            return Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None

    @staticmethod
    @database_sync_to_async
    def get_player1(game):
        """Obtener jugador 1 del juego"""
        return game.player1

    @staticmethod
    @database_sync_to_async
    def get_player2(game):
        """Obtener jugador 2 del juego"""
        return game.player2

    @staticmethod
    @database_sync_to_async
    def update_game(game, user):
        """Actualizar juego al unirse el segundo jugador"""
        game.player2 = user
        game.status = 'PLAYING'
        game.save()

    @staticmethod
    @database_sync_to_async
    def update_game_status(game, status):
        """Actualizar estado del juego"""
        game.status = status
        game.save()

    @staticmethod
    @database_sync_to_async
    def update_game_winner(game, winner_id, game_state):
        """Actualizar ganador del juego"""
        game.winner_id = winner_id
        game.score_player1 = game_state.paddles['left'].score
        game.score_player2 = game_state.paddles['right'].score
        game.status = 'FINISHED'
        game.save()