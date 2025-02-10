from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.create_game, name='create_game'),
    path('<int:game_id>/', views.join_game, name='join_game'),
]