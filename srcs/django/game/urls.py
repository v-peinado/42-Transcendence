from django.urls import path, include
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.menu_page, name='menu'),
    path('play/', views.game_page, name='game_home'),
    path('play/<int:game_id>/', views.game_page, name='game_page'),
]