from django.apps import AppConfig
from django.conf import settings
from django.db import models


class GameConfig(AppConfig):
    """App configuration"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "game"


class Game(models.Model):
    """Game model"""
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    # Player1 is who created the game
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player1",
    )
    # Player2 is who joined the game
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player2",
        null=True,	# Player2 can be null if the game is waiting for a player
    )
    score_player1 = models.IntegerField(default=0)
    score_player2 = models.IntegerField(default=0)
    # Winner is who won the game
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_won",
        null=True,
    )
    # Game status
    status = models.CharField(
        max_length=20,
        choices=[
            ("WAITING", "Waiting for players"),
            ("MATCHED", "Matched"),
            ("PLAYING", "In progress"),
            ("FINISHED", "Finished"),
        ],
        default="WAITING",
    )
    # Ready flags for players
    player1_ready = models.BooleanField(default=False)
    player2_ready = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]	# Order by created_at in descending order
