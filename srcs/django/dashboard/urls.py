from django.urls import path
from .views import player_stats_view, test_api_view, player_stats_view_by_id

urlpatterns = [
    # Endpoint que devuelve las estadísticas del jugador en formato JSON.
    # Este endpoint se utilizará para realizar peticiones AJAX y obtener los datos.
    path('player-stats/', player_stats_view, name='player_stats'),
    
    # Endpoint que renderiza la plantilla HTML para probar la API.
    # Al acceder a esta URL, se mostrará la interfaz con estilos y un botón
    # que, al hacer click, invoca la petición a '/api/player-stats/'.
    path('test-api/', test_api_view, name='test_api'),
    
    path('player-stats-id/<int:id>/', player_stats_view_by_id, name='player_stats_by_id'),
]