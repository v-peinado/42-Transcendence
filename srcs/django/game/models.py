from django.db import models
from django.conf import settings
from django.apps import AppConfig


class GameConfig(AppConfig):											# App configuration
    default_auto_field = "django.db.models.BigAutoField"
    name = "game"


class Game(models.Model):												# Database model:
    created_at = models.DateTimeField(auto_now_add=True)				# Creation date
    started_at = models.DateTimeField(null=True)						# Start date
    finished_at = models.DateTimeField(null=True)
    player1 = models.ForeignKey(										# Player 1
        settings.AUTH_USER_MODEL,										# User model
        on_delete=models.CASCADE,										# Cascade deletion (if user is deleted, game is deleted)
        related_name="games_as_player1",
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player2",
        null=True,
    )
    score_player1 = models.IntegerField(default=0)						# Players' scores
    score_player2 = models.IntegerField(default=0)
    winner = models.ForeignKey(											# Winning player
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_won",
        null=True,
    )
    status = models.CharField(											# Game status
        max_length=20,
        choices=[
            ("WAITING", "Waiting for players"),
            ("PLAYING", "In progress"),
            ("FINISHED", "Finished"),
        ],
        default="WAITING",
    )

    class Meta:															# Metaclass
        ordering = ["-created_at"]										# Order by creation date
