from django.test import TestCase
from ..engine.game_state import GameState
from ..engine.entities.ball import Ball
from ..engine.entities.paddle import Paddle

class GameLogicTests(TestCase):
    def setUp(self):
        self.game_state = GameState()

    def test_initial_game_state(self):
        """Test del estado inicial del juego"""
        self.assertEqual(self.game_state.status, 'waiting')
        self.assertEqual(self.game_state.ball.x, self.game_state.canvas_width / 2)
        self.assertEqual(self.game_state.ball.y, self.game_state.canvas_height / 2)
        
    def test_paddle_movement(self):
        """Test del movimiento de las paletas"""
        initial_y = self.game_state.paddles['left'].y
        self.game_state.move_paddle('left', 1)  # Mover hacia abajo
        self.assertGreater(self.game_state.paddles['left'].y, initial_y)
        
        initial_y = self.game_state.paddles['left'].y
        self.game_state.move_paddle('left', -1)  # Mover hacia arriba
        self.assertLess(self.game_state.paddles['left'].y, initial_y)

    def test_ball_collision_with_paddle(self):
        """Test de colisión de la pelota con las paletas"""
        # Colocar la pelota justo antes de la paleta izquierda
        self.game_state.ball.x = self.game_state.paddles['left'].x + self.game_state.paddle_width + self.game_state.ball.radius
        self.game_state.ball.y = self.game_state.paddles['left'].y + self.game_state.paddle_height / 2
        self.game_state.ball.speed_x = -5  # Moviendo hacia la izquierda
        
        # Actualizar el estado
        self.game_state.status = 'playing'
        self.game_state.update()
        
        # La pelota debería rebotar (cambiar dirección)
        self.assertGreater(self.game_state.ball.speed_x, 0)

    def test_scoring(self):
        """Test del sistema de puntuación"""
        # Mover la pelota al borde izquierdo
        self.game_state.ball.x = 0
        self.game_state.status = 'playing'
        self.game_state.update()
        
        # Debería haber un punto para el jugador derecho
        self.assertEqual(self.game_state.paddles['right'].score, 1)
        self.assertEqual(self.game_state.paddles['left'].score, 0)



# # srcs/django/game/tests/test_game_logic.py

# from django.test import TestCase
# from ..engine.game_state import GameState
# from ..engine.entities.ball import Ball
# from ..engine.entities.paddle import Paddle

# class GameLogicTests(TestCase):
#     def setUp(self):
#         """Configuración inicial para cada test"""
#         self.game_state = GameState()

#     def test_initial_state(self):
#         """Test del estado inicial del juego"""
#         self.assertEqual(self.game_state.status, 'waiting')
#         self.assertEqual(self.game_state.ball.x, self.game_state.canvas_width / 2)
#         self.assertEqual(self.game_state.ball.y, self.game_state.canvas_height / 2)
#         self.assertEqual(len(self.game_state.paddles), 2)

#     def test_paddle_movement(self):
#         """Test del movimiento de las paletas"""
#         # Mover paleta izquierda hacia arriba
#         initial_y = self.game_state.paddles['left'].y
#         self.game_state.move_paddle('left', -1)
#         self.assertLess(self.game_state.paddles['left'].y, initial_y)

#         # Mover paleta derecha hacia abajo
#         initial_y = self.game_state.paddles['right'].y
#         self.game_state.move_paddle('right', 1)
#         self.assertGreater(self.game_state.paddles['right'].y, initial_y)

#     def test_ball_collision_with_walls(self):
#         """Test de colisiones de la pelota con paredes"""
#         self.game_state.status = 'playing'
#         self.game_state.ball.y = 0
#         self.game_state.ball.speed_y = -5
#         self.game_state.update()
#         self.assertGreater(self.game_state.ball.speed_y, 0)

#     def test_ball_collision_with_paddle(self):
#         """Test de colisiones de la pelota con las paletas"""
#         self.game_state.status = 'playing'
        
#         # Colocar la pelota cerca de la paleta izquierda
#         self.game_state.ball.x = self.game_state.paddles['left'].x + self.game_state.paddle_width + 1
#         self.game_state.ball.y = self.game_state.paddles['left'].y + self.game_state.paddle_height / 2
#         self.game_state.ball.speed_x = -5
        
#         initial_speed = abs(self.game_state.ball.speed_x)
#         self.game_state.update()
        
#         # Verificar que la pelota rebotó y aumentó su velocidad
#         self.assertGreater(abs(self.game_state.ball.speed_x), initial_speed)

#     def test_scoring(self):
#         """Test del sistema de puntuación"""
#         self.game_state.status = 'playing'
        
#         # Punto para el jugador derecho
#         self.game_state.ball.x = 0
#         self.game_state.update()
#         self.assertEqual(self.game_state.paddles['right'].score, 1)
#         self.assertEqual(self.game_state.paddles['left'].score, 0)
        
#         # Punto para el jugador izquierdo
#         self.game_state.ball.x = self.game_state.canvas_width
#         self.game_state.update()
#         self.assertEqual(self.game_state.paddles['right'].score, 1)
#         self.assertEqual(self.game_state.paddles['left'].score, 1)

#     def test_game_state_serialization(self):
#         """Test de la serialización del estado del juego"""
#         state_dict = self.game_state.serialize()
        
#         self.assertIn('ball', state_dict)
#         self.assertIn('paddles', state_dict)
#         self.assertIn('status', state_dict)
        
#         # Verificar datos de la pelota
#         self.assertIn('x', state_dict['ball'])
#         self.assertIn('y', state_dict['ball'])
        
#         # Verificar datos de las paletas
#         self.assertIn('left', state_dict['paddles'])
#         self.assertIn('right', state_dict['paddles'])