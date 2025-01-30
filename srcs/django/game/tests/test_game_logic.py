# from django.test import TestCase
# from ..engine.game_state import GameState
# from ..engine.entities.ball import Ball
# from ..engine.entities.paddle import Paddle

# class GameLogicTests(TestCase):
#     def setUp(self):
#         self.game_state = GameState()

#     def test_initial_game_state(self):
#         """Test del estado inicial del juego"""
#         self.assertEqual(self.game_state.status, 'waiting')
#         self.assertEqual(self.game_state.ball.x, self.game_state.canvas_width / 2)
#         self.assertEqual(self.game_state.ball.y, self.game_state.canvas_height / 2)
        
#     def test_paddle_movement(self):
#         """Test del movimiento de las paletas"""
#         initial_y = self.game_state.paddles['left'].y
#         self.game_state.move_paddle('left', 1)  # Mover hacia abajo
#         self.assertGreater(self.game_state.paddles['left'].y, initial_y)
        
#         initial_y = self.game_state.paddles['left'].y
#         self.game_state.move_paddle('left', -1)  # Mover hacia arriba
#         self.assertLess(self.game_state.paddles['left'].y, initial_y)

#     def test_ball_collision_with_paddle(self):
#         """Test de colisión de la pelota con las paletas"""
#         # Colocar la pelota justo antes de la paleta izquierda
#         self.game_state.ball.x = self.game_state.paddles['left'].x + self.game_state.paddle_width + self.game_state.ball.radius
#         self.game_state.ball.y = self.game_state.paddles['left'].y + self.game_state.paddle_height / 2
#         self.game_state.ball.speed_x = -5  # Moviendo hacia la izquierda
        
#         # Actualizar el estado
#         self.game_state.status = 'playing'
#         self.game_state.update()
        
#         # La pelota debería rebotar (cambiar dirección)
#         self.assertGreater(self.game_state.ball.speed_x, 0)

#     def test_scoring(self):
#         """Test del sistema de puntuación"""
#         # Mover la pelota al borde izquierdo
#         self.game_state.ball.x = 0
#         self.game_state.status = 'playing'
#         self.game_state.update()
        
#         # Debería haber un punto para el jugador derecho
#         self.assertEqual(self.game_state.paddles['right'].score, 1)
#         self.assertEqual(self.game_state.paddles['left'].score, 0)