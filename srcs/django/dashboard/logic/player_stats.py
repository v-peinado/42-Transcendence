from django.db.models import Sum
from game.models import Game
from django.db.models import Q

def get_player_stats(user):
    games_played = Game.objects.filter(player1=user).count() + Game.objects.filter(player2=user).count()
    games_won = Game.objects.filter(winner=user).count()
    win_ratio = (games_won / games_played) * 100 if games_played > 0 else 0
    total_points_scored = Game.objects.filter(player1=user).aggregate(Sum('score_player1'))['score_player1__sum'] or 0
    total_points_scored += Game.objects.filter(player2=user).aggregate(Sum('score_player2'))['score_player2__sum'] or 0
    total_points_conceded = Game.objects.filter(player1=user).aggregate(Sum('score_player2'))['score_player2__sum'] or 0
    total_points_conceded += Game.objects.filter(player2=user).aggregate(Sum('score_player1'))['score_player1__sum'] or 0
    avg_points_per_game = total_points_scored / games_played if games_played > 0 else 0

    if user.profile_image:
        profile_picture_url = user.profile_image.url
    elif user.fortytwo_image:
        profile_picture_url = user.fortytwo_image
    else:
        profile_picture_url = user.DEFAULT_PROFILE_IMAGE.format(user.username)

    return {
        'username': user.username,
        'games_played': games_played,
        'games_won': games_won,
        'win_ratio': win_ratio,
        'avg_points_per_game': avg_points_per_game,
        'total_points_scored': total_points_scored,
        'total_points_conceded': total_points_conceded,
        'profile_picture_url': profile_picture_url,
    }

def get_player_games(user):
    games = Game.objects.filter(
        Q(player1=user) | Q(player2=user)
    )
    games = games.exclude(
        Q(score_player1=0) & Q(score_player2=0)
    )
    return games