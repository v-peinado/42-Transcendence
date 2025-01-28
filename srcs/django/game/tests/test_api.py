from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Game
from rest_framework.test import APIClient

User = get_user_model()

class GameAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='player1', password='test123')
        self.user2 = User.objects.create_user(username='player2', password='test123')
        self.client.force_authenticate(user=self.user1)

    def test_create_game(self):
        """Test de creación de partida"""
        response = self.client.post(reverse('game:create_game'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('game_id' in response.json())
        
    def test_join_game(self):
        """Test para unirse a una partida"""
        # Crear una partida primero
        game = Game.objects.create(player1=self.user1, status='WAITING')
        
        # Intentar unirse con otro usuario
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(reverse('game:join_game', args=[game.id]))
        
        self.assertEqual(response.status_code, 200)
        game.refresh_from_db()
        self.assertEqual(game.player2, self.user2)
        self.assertEqual(game.status, 'PLAYING')

    def test_game_status(self):
        """Test para obtener el estado de una partida"""
        game = Game.objects.create(
            player1=self.user1,
            player2=self.user2,
            status='PLAYING'
        )
        
        response = self.client.get(reverse('game:game_status', args=[game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'PLAYING')