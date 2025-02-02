from django.db import models
from django.conf import settings
from django.apps import AppConfig

class GameConfig(AppConfig):								# Configuración de la app
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'game'

class Game(models.Model):									# Modelo para la base de datos:
    created_at = models.DateTimeField(auto_now_add=True)	# Fecha de creación
    started_at = models.DateTimeField(null=True)			# Fecha de inicio
    finished_at = models.DateTimeField(null=True)
    player1 = models.ForeignKey(							# Jugador 1
        settings.AUTH_USER_MODEL,							# Modelo de usuario
        on_delete=models.CASCADE,							# Borrar en cascada (eso es, si se borra el usuario, se borra el juego)
        related_name='games_as_player1'
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player2',
        null=True
    )
    score_player1 = models.IntegerField(default=0)			# Puntos de los jugadores
    score_player2 = models.IntegerField(default=0)
    winner = models.ForeignKey(								# Jugador ganador
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_won',
        null=True
    )
    status = models.CharField(								# Estado del juego
        max_length=20,
        choices=[
            ('WAITING', 'Waiting for players'),
            ('PLAYING', 'In progress'),
            ('FINISHED', 'Finished')
        ],
        default='WAITING'
    )
    game_mode = models.CharField(							# Modo de juego
        max_length=20,
        choices=[
            ('SINGLE', 'Single Player'),
            ('MULTI', 'Multiplayer')
        ],
        default='MULTI'
    )
    difficulty = models.CharField(							# Dificultad
        max_length=20,
        choices=[
            ('easy', 'Fácil'),
            ('medium', 'Intermedio'),
            ('hard', 'Difícil'),
            ('nightmare', 'Nightmare')
        ],
        null=True,											# Permitir null para modo multiplayer (no se necesita dificultad en modo multiplayer)
        blank=True											# Permitir vacío en el formulario (no se necesita dificultad en modo multiplayer)
    )

    class Meta:												# Metaclase
        ordering = ['-created_at']							# Ordenar por fecha de creación