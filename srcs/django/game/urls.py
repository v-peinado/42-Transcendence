from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_view, name='create_game'),
    path('<int:game_id>/', views.game_view, name='join_game'),
]