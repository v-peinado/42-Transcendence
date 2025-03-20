from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .logic.player_stats import get_player_stats, get_player_games
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def player_stats_view(request):
    """
    Endpoint to get player statistics in JSON format.
    It will be used for asynchronous requests (fetch) from the front-end.
    """
    user = request.user
    stats = get_player_stats(user)
    games = get_player_games(user)
    games_list = [
        {
            'player1': game.player1.username,
            'player2': game.player2.username,
            'score_player1': game.score_player1,
            'score_player2': game.score_player2,
            'winner': game.winner.username if game.winner else None,
            'date': game.created_at.isoformat() if game.created_at else None
        }
        for game in games
    ]
    return JsonResponse({'stats': stats, 'games': games_list})

@login_required
def player_stats_view_by_id(request, id):
    user = get_object_or_404(User, pk=id)
    stats = get_player_stats(user)
    games = get_player_games(user)

     # Añadido por Ampi para poder ver las fotos de usuarios
    stats['username'] = user.username
    stats['profile_image'] = user.profile_image.url if user.profile_image else None
    stats['fortytwo_image'] = user.fortytwo_image if user.fortytwo_image else None
    stats['avatar'] = f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.username}"
    
    games_list = [
        {
            'player1': game.player1.username,
            'player2': game.player2.username,
            'score_player1': game.score_player1,
            'score_player2': game.score_player2,
            'winner': game.winner.username if game.winner else None,
            'date': game.created_at.isoformat() if game.created_at else None
        }
        for game in games
    ]
    return JsonResponse({'stats': stats, 'games': games_list})

@login_required
def test_api_view(request):
    """
    Endpoint that renders the HTML template to test the API.
    This view shows a styled interface (with Bootstrap) that includes
    a button to invoke the request to 'player_stats_view' and display
    the player's statistics.
    """
    return render(request, 'dashboard/test_api.html')
