from django.urls import path, include
from . import views

app_name = 'game'

urlpatterns = [
    path('api/', include('game.api.urls')),  # Endpoints de API
    path('play/<int:game_id>/', views.game_page, name='game_page'),
    path('play/', views.game_page, name='game_home'),
]