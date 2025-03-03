from django.db import models
from django.conf import settings
from django.apps import AppConfig


class GameConfig(AppConfig):  # App configuration
    default_auto_field = "django.db.models.BigAutoField"
    name = "game"


class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player1",
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player2",
        null=True,
    )
    score_player1 = models.IntegerField(default=0)
    score_player2 = models.IntegerField(default=0)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_won",
        null=True,
    )
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
    # Campos para marcar que cada jugador se ha unido (listo)
    player1_ready = models.BooleanField(default=False)
    player2_ready = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
