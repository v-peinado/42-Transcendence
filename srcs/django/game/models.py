from django.db import models
from django.conf import settings
from django.urls import re_path
from .consumers import GameConsumer, MatchmakingConsumer

class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player1'
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player2'
    )
    score_player1 = models.IntegerField(default=0)
    score_player2 = models.IntegerField(default=0)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_won',
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('WAITING', 'Waiting for players'),
            ('PLAYING', 'In progress'),
            ('FINISHED', 'Finished')
        ],
        default='WAITING'
    )

    class Meta:
        ordering = ['-created_at']