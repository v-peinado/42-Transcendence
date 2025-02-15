from tournament.models import Tournament, TournamentMatch, TemporaryPlayer
from django.contrib.auth import get_user_model
from itertools import combinations
from datetime import datetime, timedelta
import pytz
from django.conf import settings

User = get_user_model()

def create_tournament(name, creator_id, max_match_points, number_of_players, participants):
    number_of_players = int(number_of_players)
    if len(participants) != number_of_players:
        raise ValueError(f"El número de participantes no coincide con el número de jugadores especificado: {len(participants)} vs {number_of_players}")
    
    creator = User.objects.get(id=creator_id)
    tournament = Tournament.objects.create(
        name=name,
        creator=creator,
        max_match_points=max_match_points,
        number_of_players=number_of_players
    )
    add_users_to_tournament(tournament, participants)
    create_tournament_matches(tournament)
    return tournament

def add_users_to_tournament(tournament, participants):
    for participant_username in participants:
        TemporaryPlayer.objects.create(username=participant_username, tournament=tournament)
    #TemporaryPlayer.objects.create(username=tournament.creator.username, tournament=tournament)

def create_tournament_matches(tournament):
    participants = list(tournament.temporary_players.all())
    for player1, player2 in combinations(participants, 2):
        TournamentMatch.objects.create(
            tournament=tournament,
            player1=player1,
            player2=player2,
        )

def check_tournament_winner(tournament):
    matches = tournament.matches.all()
    if all(match.played for match in matches):
        players = tournament.temporary_players.all()
        player_wins = {player: 0 for player in players}
        player_received_points = {player: 0 for player in players}
        for match in matches:
            if match.winner:
                player_wins[match.winner] += 1
            player_received_points[match.player1] += match.player2_points
            player_received_points[match.player2] += match.player1_points
        max_wins = max(player_wins.values())
        potential_winners = [player for player, wins in player_wins.items() if wins == max_wins]
        if len(potential_winners) == 1:
            tournament.winner = potential_winners[0]
        else:
            tournament.winner = min(potential_winners, key=lambda player: player_received_points[player])
        tournament.finished = True
        tournament.save()

def get_user_tournaments(user_id):
    user = User.objects.get(id=user_id)
    tournaments = Tournament.objects.filter(creator=user)
    ongoing_tournaments = [t for t in tournaments if not all(match.winner for match in t.matches.all())]
    return ongoing_tournaments

