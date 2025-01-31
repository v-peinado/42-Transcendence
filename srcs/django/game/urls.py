from django.urls import path, include
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_page, name='game_home'),				# URL raíz del juego
    path('<int:game_id>/', views.game_page, name='game_page'),	# URL específica de una partida
]