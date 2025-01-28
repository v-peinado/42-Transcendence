# from django.urls import path
# from . import views

# app_name = 'game_api'

# urlpatterns = [
#     path('games/create/', views.create_game, name='create_game'),
#     path('games/<int:game_id>/join/', views.join_game, name='join_game'),
#     path('games/<int:game_id>/status/', views.game_status, name='game_status'),
# ]

# srcs/django/game/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')

urlpatterns = [
    path('', include(router.urls)),
]