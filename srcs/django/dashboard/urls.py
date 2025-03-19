from django.urls import path
from .views import player_stats_view, test_api_view, player_stats_view_by_id

urlpatterns = [
    path('player-stats/', player_stats_view, name='player_stats'),
    
    path('test-api/', test_api_view, name='test_api'),
    
    path('player-stats-id/<int:id>/', player_stats_view_by_id, name='player_stats_by_id'),
]