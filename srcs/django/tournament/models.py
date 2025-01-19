from django.db import models
from django.utils import timezone
from django.conf import settings

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_ongoing = models.BooleanField(default=True)
    match_time_limit = models.IntegerField(help_text="Tiempo para celebrar una partida en minutos")
    current_round = models.IntegerField(default=1, help_text="Ronda actual del torneo")
    total_rounds = models.IntegerField(help_text="Número total de rondas en el torneo")

    def save(self, *args, **kwargs):
        if not self.is_ongoing and not self.end_date:
            self.end_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, related_name='matches')
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='matches_as_user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='matches_as_user2')
    score_user1 = models.IntegerField(null=True, blank=True)
    score_user2 = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user1.username if self.user1 else 'Deleted User'} vs {self.user2.username if self.user2 else 'Deleted User'} in {self.tournament.name if self.tournament else 'Deleted Tournament'}"

class TournamentMatch(models.Model):
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, related_name='tournament_matches')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, related_name='tournament_matches')
    round = models.IntegerField(help_text="Ronda del torneo a la que pertenece el partido")
    is_played = models.BooleanField(default=False)

    def __str__(self):
        return f"Match {self.match.id if self.match else 'Deleted Match'} in {self.tournament.name if self.tournament else 'Deleted Tournament'}, Round {self.round}"
    
class PlayerTournament(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='player_tournaments')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, related_name='player_tournaments')
    place = models.IntegerField(null=True, blank=True, help_text="Ronda a la que se ha llegado en el torneo")

    def __str__(self):
        return f"Player {self.player.username if self.player else 'Deleted Player'} in {self.tournament.name if self.tournament else 'Deleted Tournament'}"