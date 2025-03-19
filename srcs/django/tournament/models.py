from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_tournaments', on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True)
    max_match_points = models.IntegerField()
    number_of_players = models.IntegerField(
        validators=[
            MinValueValidator(2),  # Assuming you need at least 2 players
            MaxValueValidator(10)  # Example: max 16 players
        ]
    )
    finished = models.BooleanField(default=False)
    winner = models.CharField(max_length=50, null=True, blank=True)

class TemporaryPlayer(models.Model):
    tournament = models.ForeignKey(Tournament, related_name='temporary_players', on_delete=models.CASCADE)
    username = models.CharField(max_length=50)

class TournamentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, related_name='matches', on_delete=models.CASCADE)
    player1 = models.ForeignKey(TemporaryPlayer, related_name='matches_as_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(TemporaryPlayer, related_name='matches_as_player2', on_delete=models.CASCADE)
    winner = models.ForeignKey(TemporaryPlayer, related_name='won_matches', null=True, blank=True, on_delete=models.SET_NULL)
    player1_points = models.IntegerField(default=0)
    player2_points = models.IntegerField(default=0)
    player1_received_points = models.IntegerField(default=0)
    player2_received_points = models.IntegerField(default=0)
    played = models.BooleanField(default=False)