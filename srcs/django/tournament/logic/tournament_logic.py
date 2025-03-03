from tournament.models import Tournament, TournamentMatch, TemporaryPlayer
from chat.consumers.notifications import NotificationsConsumer
from django.contrib.auth import get_user_model
from itertools import combinations
from datetime import datetime, timedelta
import pytz
from django.conf import settings

User = get_user_model()
import logging

logger = logging.getLogger(__name__)

# python
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

    # Notificar creación de torneo, mostrando las partidas planificadas (sin notificar cada partida por separado)
    participants_str = ', '.join(participants)
    matches_str = ', '.join(f"{m.player1.username} vs {m.player2.username}" for m in tournament.matches.all())
    NotificationsConsumer.send_notification(
        creator.id,
        f"Se ha creado el torneo '{tournament.name}' con participantes: {participants_str}.\n\n "
        f"Total de partidas: {tournament.matches.count()}.\n\nPartidas planificadas: {matches_str}."
    )

    return tournament

def add_users_to_tournament(tournament, participants):
    for participant in participants:
        TemporaryPlayer.objects.create(username=participant, tournament=tournament)

def create_tournament_matches(tournament):
    participants = list(tournament.temporary_players.all())
    for player1, player2 in combinations(participants, 2):
        TournamentMatch.objects.create(
            tournament=tournament,
            player1=player1,
            player2=player2,
        )
    # No notifiques aquí para no saturar. Se notificará al comienzo del torneo y luego partida a partida.

def start_tournament(tournament):
    """
    Función opcional para marcar el inicio oficial del torneo y avisar sólo la primera partida.
    """
    NotificationsConsumer.send_notification(
        tournament.creator.id,
        f"El torneo '{tournament.name}' ha empezado."
    )
    # Notificar sólo la primera partida disponible
    notify_next_match(tournament)

def start_match(match):
    NotificationsConsumer.send_notification(
        match.tournament.creator.id,
        f"La partida {match.player1.username} vs {match.player2.username} ha comenzado."
    )

def update_match_result(match, winner):
    match.winner = winner
    match.played = True
    match.save()
    NotificationsConsumer.send_notification(
        match.tournament.creator.id,
        f"La partida {match.player1.username} vs {match.player2.username} terminó. Ganó {winner.username}."
    )
    notify_next_match(match.tournament)
def check_tournament_winner(tournament):
    logger.info(f"Checking tournament winner for tournament ID: {tournament.id}")
    matches = tournament.matches.all()
    if all(match.played for match in matches):
        logger.info("All matches have been played.")
        players = tournament.temporary_players.all()
        player_wins = {p: 0 for p in players}
        player_received_points = {p: 0 for p in players}
        for match in matches:
            if match.winner:
                player_wins[match.winner] += 1
            player_received_points[match.player1] += match.player2_points
            player_received_points[match.player2] += match.player1_points

        logger.debug(f"Player wins: {player_wins}")
        logger.debug(f"Player received points: {player_received_points}")

        max_wins = max(player_wins.values())
        potential_winners = [p for p, w in player_wins.items() if w == max_wins]
        logger.debug(f"Potential winners: {potential_winners}")

        if len(potential_winners) == 1:
            winner = potential_winners[0]
        else:
            winner = min(potential_winners, key=lambda p: player_received_points[p])
        
        logger.info(f"Tournament winner determined: {winner.username}")

        tournament.winner = winner.username  # Guardar el nombre del ganador
        tournament.finished = True
        tournament.save()
        logger.info(f"Tournament ID: {tournament.id} marked as finished.")

        NotificationsConsumer.send_notification(
            tournament.creator.id,
            f"El torneo '{tournament.name}' ha finalizado. Ganador: {winner.username}."
        )
        logger.info(f"Notification sent for tournament ID: {tournament.id}")
    else:
        logger.info("Not all matches have been played yet.")


def notify_next_match(tournament):
    """
    Notifica solo la próxima partida pendiente en orden.
    Llamar después de acabar una partida o al iniciar el torneo por primera vez.
    """
    pendientes = tournament.matches.filter(played=False).order_by('id')
    if pendientes.exists():
        next_match = pendientes.first()
        NotificationsConsumer.send_notification(
            tournament.creator.id,
            f"La siguiente partida será {next_match.player1.username} vs {next_match.player2.username}."
        )

def get_user_tournaments(user_id):
    user = User.objects.get(id=user_id)
    tournaments = Tournament.objects.filter(creator=user)
    return [t for t in tournaments if not all(m.winner for m in t.matches.all())]