from django.urls import path
from .views import PlayedTournamentsView, PendingTournamentsView, TournamentMenuView, CurrentUserView, CreateTournamentView, DeleteTournamentView, StartTournamentView, StartMatchView, TournamentMatchesView, DetermineTournamentWinnerView, TournamentDetailView, StartMatchNotificationView, GetTournamentWinnerView

urlpatterns = [
    path('', TournamentMenuView.as_view(), name='tournament_menu'),
    path('played_tournaments/', PlayedTournamentsView.as_view(), name='played_tournaments'),
    path('pending_tournaments/', PendingTournamentsView.as_view(), name='pending_tournaments'),
    path('current_user/', CurrentUserView.as_view(), name='current_user'),
    path('create_tournament/', CreateTournamentView.as_view(), name='create_tournament'),
    path('delete_tournament/<int:tournament_id>/', DeleteTournamentView.as_view(), name='delete_tournament'),
    path('start_tournament/<int:tournament_id>/', StartTournamentView.as_view(), name='start_tournament'),
    path('start_match/<int:match_id>/', StartMatchView.as_view(), name='start_match'),
    path('tournament_matches/<int:tournament_id>/', TournamentMatchesView.as_view(), name='tournament_matches'),
    path('determine_winner/<int:tournament_id>/', DetermineTournamentWinnerView.as_view(), name='determine_winner'),
    path('tournament_detail/<int:tournament_id>/', TournamentDetailView.as_view(), name='tournament-detail'),
    path('start_match_notification/<int:match_id>/', StartMatchNotificationView.as_view(), name='start_match_notification'),
    path('get_winner/<int:tournament_id>/', GetTournamentWinnerView.as_view(), name='get_winner'),
]