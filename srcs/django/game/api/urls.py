from django.urls import path
from . import views

app_name = 'game_api'

urlpatterns = [
    path('games/create/', views.create_game, name='create_game'),
    path('games/<int:game_id>/join/', views.join_game, name='join_game'),
    path('games/<int:game_id>/status/', views.game_status, name='game_status'),
]