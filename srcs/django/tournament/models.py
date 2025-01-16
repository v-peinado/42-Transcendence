from django.db import models
from django.utils import timezone
from django.conf import settings

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_ongoing = models.BooleanField(default=True)
    match_time_limit = models.IntegerField(help_text="Tiempo para celebrar una partida en minutos")

    def save(self, *args, **kwargs):
        if not self.is_ongoing and not self.end_date:
            self.end_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_as_user2')
    score_user1 = models.IntegerField(null=True, blank=True)
    score_user2 = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user1.username} vs {self.user2.username} in {self.tournament.name}"

class TournamentMatch(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='tournament_matches')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='tournament_matches')

    def __str__(self):
        return f"Match {self.match.id} in {self.tournament.name}"
    
class PlayerTournament(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='player_tournaments')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='player_tournaments')
    place = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Player {self.player.username} in {self.tournament.name}"