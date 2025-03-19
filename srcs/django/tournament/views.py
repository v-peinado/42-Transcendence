from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import json
from .models import Tournament, TournamentMatch, TemporaryPlayer
from .logic.tournament_logic import create_tournament, check_tournament_winner, start_tournament, start_match, update_match_result, notify_next_match

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TournamentMenuView(View):
    def get(self, request):
        return render(request, 'tournament_menu.html')

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class PlayedTournamentsView(View):
    def get(self, request):
        user = request.user
        tournaments = Tournament.objects.filter(finished=True, creator=user)
        data = []
        for tournament in tournaments:
            winner = None
            matches = tournament.matches.all()
            if matches and all(match.winner for match in matches):
                winner = max(matches, key=lambda m: m.player1_points + m.player2_points).winner
            data.append({
                'id': tournament.id,
                'name': tournament.name,
                'participants': [{'id': p.id, 'username': p.username} for p in tournament.temporary_players.all()],
                'winner': {'id': winner.id, 'username': winner.username} if winner else 'TBD'
            })
        return JsonResponse(data, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class PendingTournamentsView(View):
    def get(self, request):
        user = request.user
        tournaments = Tournament.objects.filter(finished=False, creator=user)
        data = []
        for tournament in tournaments:
            pending_matches = [match for match in tournament.matches.all() if not match.winner]
            if pending_matches:
                data.append({
                    'id': tournament.id,
                    'name': tournament.name,
                    'creator': {'id': tournament.creator.id, 'username': tournament.creator.username},
                    'max_match_points': tournament.max_match_points,
                    'participants': [{'id': p.id, 'username': p.username} for p in tournament.temporary_players.all()],
                    'pending_matches': [{
                        'id': match.id,
                        'player1': {'id': match.player1.id, 'username': match.player1.username},
                        'player2': {'id': match.player2.id, 'username': match.player2.username}
                    } for match in pending_matches]
                })
        return JsonResponse(data, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CurrentUserView(View):
    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
        return JsonResponse(data)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CreateTournamentView(View):
    def post(self, request):
        data = json.loads(request.body)
        name = data.get('name')
        creator_id = request.user.id
        max_match_points = data.get('max_match_points')
        number_of_players = data.get('number_of_players')
        participants = data.get('participants')

        if len(participants) != number_of_players:
            return JsonResponse({'error': 'Number of participants does not match the number of players'}, status=400)

        if len(participants) != len(set(participants)):
            return JsonResponse({'error': 'Participant names must be unique'}, status=400)

        try:
            tournament = create_tournament(
                name=name,
                creator_id=creator_id,
                max_match_points=max_match_points,
                number_of_players=number_of_players,
                participants=participants
            )
            return JsonResponse({'message': 'Tournament created successfully', 'tournament_id': tournament.id})
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class DeleteTournamentView(View):
    def delete(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, id=tournament_id)
        tournament.delete()
        return JsonResponse({'message': 'Torneo eliminado correctamente'})

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class StartTournamentView(View):
    def post(self, request, tournament_id):
        user = request.user
        if not Tournament.objects.filter(id=tournament_id, creator=user).exists():
            return JsonResponse({'error': 'No tienes permiso para ver los partidos de este torneo'}, status=403)
        tournament = get_object_or_404(Tournament, id=tournament_id)
        tournament.started = True
        tournament.save()
        start_tournament(tournament)
        return JsonResponse({'message': 'Torneo empezado correctamente'})

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')  
class StartMatchNotificationView(View):
    def post(self, request, match_id):
        user = request.user
        if not Tournament.objects.filter(creator=user).exists():
            return JsonResponse({'error': 'No tienes permiso para ver los partidos de este torneo'}, status=403)
        match = get_object_or_404(TournamentMatch, id=match_id)
        
        start_match(match)
        
        return JsonResponse({'message': 'Partida iniciada correctamente'})

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch') 
class StartMatchView(View):
    def post(self, request, match_id):
        data = json.loads(request.body)
        match = get_object_or_404(TournamentMatch, id=match_id)
        match.player1_points = data['player1Points']
        match.player2_points = data['player2Points']
        match.player1_received_points = data['player2Points']
        match.player2_received_points = data['player1Points']
        max_points = match.tournament.max_match_points

        if match.player1_points >= max_points:
            match.winner = match.player1
            match.played = True
        elif match.player2_points >= max_points:
            match.winner = match.player2
            match.played = True

        match.save()
        if match.played:
            update_match_result(match, match.winner) 
        return JsonResponse({'message': 'Partida guardada correctamente'})
    
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class DetermineTournamentWinnerView(View):
    def post(self, request, tournament_id):
        user = request.user
        if not Tournament.objects.filter(id=tournament_id, creator=user).exists():
            return JsonResponse({'error': 'No tienes permiso para ver los partidos de este torneo'}, status=403)
        tournament = get_object_or_404(Tournament, id=tournament_id)
        check_tournament_winner(tournament)
        
        return JsonResponse({'message': 'Ganador del torneo determinado correctamente'})

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class GetTournamentWinnerView(View):
    def get(self, request, tournament_id):
        user = request.user
        if not Tournament.objects.filter(id=tournament_id, creator=user).exists():
            return JsonResponse({'error': 'No tienes permiso para ver los partidos de este torneo'}, status=403)
        tournament = get_object_or_404(Tournament, id=tournament_id)
        if tournament.winner:
            winner = tournament.winner
            return JsonResponse({'winner': winner})
        else:
            return JsonResponse({'error': 'El torneo no tiene un ganador aún.'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TournamentMatchesView(View):
    def get(self, request, tournament_id):
        user = request.user
        if not Tournament.objects.filter(id=tournament_id, creator=user).exists():
            return JsonResponse({'error': 'No tienes permiso para ver los partidos de este torneo'}, status=403)
        matches = TournamentMatch.objects.filter(tournament_id=tournament_id)
        data = [{
            'id': match.id,
            'player1': {'id': match.player1.id, 'username': match.player1.username},
            'player2': {'id': match.player2.id, 'username': match.player2.username},
            'player1_points': match.player1_points,
            'player2_points': match.player2_points,
            'winner': match.winner.username if match.winner else None,
            'played': match.played,
        } for match in matches]
        return JsonResponse(data, safe=False)
    
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch') 
class TournamentDetailView(View):
    def get(self, request, tournament_id):
        user = request.user
        if not Tournament.objects.filter(id=tournament_id, creator=user).exists():
            return JsonResponse({'error': 'No tienes permiso para ver este torneo'}, status=403)
        tournament = get_object_or_404(Tournament, id=tournament_id)
        data = {
            'id': tournament.id,
            'name': tournament.name,
            'creator': {'id': tournament.creator.id, 'username': tournament.creator.username},
            'max_match_points': tournament.max_match_points,
            'participants': [{'id': p.id, 'username': p.username} for p in tournament.temporary_players.all()],
            'matches': [{
                'id': match.id,
                'player1': {'id': match.player1.id, 'username': match.player1.username},
                'player2': {'id': match.player2.id, 'username': match.player2.username},
                'winner': {'id': match.winner.id, 'username': match.winner.username} if match.winner else None,
                'player1_points': match.player1_points,
                'player2_points': match.player2_points
            } for match in tournament.matches.all()],
            'finished': tournament.finished,
            'winner': tournament.winner 
        }
        return JsonResponse(data)