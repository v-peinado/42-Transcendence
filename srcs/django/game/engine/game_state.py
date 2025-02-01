from .entities.ball import Ball
from .entities.paddle import Paddle
import random
import time

class GameState:
    # Modificar la configuración de dificultad para que coincida con la original
    DIFFICULTY_SETTINGS = {
        'easy': {
            'RANDOMNESS': 60,
            'MISS_CHANCE': 0.3,
            'AI_REACTION_DELAY': 300,
            'BALL_SPEED': 7
        },
        'medium': {
            'RANDOMNESS': 40,
            'MISS_CHANCE': 0.1,
            'AI_REACTION_DELAY': 200,
            'BALL_SPEED': 7
        },
        'hard': {
            'RANDOMNESS': 20,
            'MISS_CHANCE': 0.05,
            'AI_REACTION_DELAY': 100,
            'BALL_SPEED': 9
        }
    }

    def __init__(self, canvas_width=800, canvas_height=400):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Inicializar pelota en el centro
        self.ball = Ball(canvas_width/2, canvas_height/2)
        
        # Inicializar paletas
        paddle_height = 100
        self.paddles = {
            'left': Paddle(
                x=10,
                y=(canvas_height - paddle_height) / 2,  # Centrar verticalmente
                height=paddle_height
            ),
            'right': Paddle(
                x=canvas_width - 20,
                y=(canvas_height - paddle_height) / 2,  # Centrar verticalmente
                height=paddle_height
            )
        }
        
        self.status = 'waiting'
        self.countdown = 3  # Añadimos contador de 3 segundos
        self.countdown_active = False
        self.is_single_player = False
        self.difficulty = 'medium'
        self.last_ai_update = 0  # Añadir timestamp para controlar frecuencia de actualización
        self.ai_update_interval = 1.0  # 1000ms como en el original
        self.ai_target_y = None
        
    def start_countdown(self):
        self.countdown = 3
        self.countdown_active = True
        self.status = 'countdown'
        
    def update(self, timestamp=None):
        if self.countdown_active:
            return  # No actualizar la pelota durante el countdown

        if self.status != 'playing':
            return
            
        # Actualizar pelota
        self.ball.update(self.canvas_width, self.canvas_height)
        
        # IA para modo single player con control de frecuencia
        if self.is_single_player and timestamp:
            if timestamp - self.last_ai_update >= self.ai_update_interval:
                self._update_ai()
                self.last_ai_update = timestamp
            
        # Verificar colisiones con paletas
        self._check_paddle_collisions()
        
        # Verificar puntuación
        self._check_scoring()
        
    def _check_paddle_collisions(self):
        # Colisión con paleta izquierda
        if (self.ball.x - self.ball.radius <= self.paddles['left'].x + self.paddles['left'].width and
            self.paddles['left'].y <= self.ball.y <= self.paddles['left'].y + self.paddles['left'].height):
            self.ball.x = self.paddles['left'].x + self.paddles['left'].width + self.ball.radius
            self.ball.speed_x = abs(self.ball.speed_x)
            
        # Colisión con paleta derecha
        if (self.ball.x + self.ball.radius >= self.paddles['right'].x and
            self.paddles['right'].y <= self.ball.y <= self.paddles['right'].y + self.paddles['right'].height):
            self.ball.x = self.paddles['right'].x - self.ball.radius
            self.ball.speed_x = -abs(self.ball.speed_x)
            
    def _check_scoring(self):
        # Punto para jugador derecho
        if self.ball.x < 0:
            self.paddles['right'].score += 1
            self._reset_ball('right')
            
        # Punto para jugador izquierdo
        elif self.ball.x > self.canvas_width:
            self.paddles['left'].score += 1
            self._reset_ball('left')
            
    def _reset_ball(self, scoring_side):
        self.ball.reset(self.canvas_width/2, self.canvas_height/2)
        
    def move_paddle(self, side, direction):
        """
        Mueve una paleta en una dirección
        side: 'left' o 'right'
        direction: -1 (arriba), 0 (parar), 1 (abajo)
        """
        if side in self.paddles:
            paddle = self.paddles[side]
            current_y = paddle.y  # Guardar posición actual
            paddle.move(direction, self.canvas_height)
            print(f"GameState: paddle {side} moved from {current_y} to {paddle.y}")

    def serialize(self):
        current_state = {
            'ball': self.ball.serialize(),
            'paddles': {
                side: {
                    'x': paddle.x,
                    'y': paddle.y,  # Asegurarnos de usar el valor actual
                    'width': paddle.width,
                    'height': paddle.height,
                    'score': paddle.score
                }
                for side, paddle in self.paddles.items()
            },
            'status': self.status,
            'canvas': {
                'width': self.canvas_width,
                'height': self.canvas_height
            }
        }
        
        if self.countdown_active:
            current_state['countdown'] = self.countdown
            
        print(f"Serializing paddle positions - Left: {current_state['paddles']['left']['y']}, Right: {current_state['paddles']['right']['y']}")
        return current_state

    def _update_ai(self):
        """
        Implementación de la IA basada en el código original de JavaScript
        """
        current_time = time.time() * 1000  # Convertir a milisegundos
        
        if current_time - self.last_ai_update >= self.ai_update_interval:
            self.last_ai_update = current_time
            settings = self.DIFFICULTY_SETTINGS[self.difficulty]
            paddle = self.paddles['right']
            
            # Predecir posición de la pelota
            predicted_y = self._predict_ball_y()
            
            # Añadir aleatoriedad como en el original
            randomness = (random.random() * settings['RANDOMNESS']) - (settings['RANDOMNESS'] / 2)
            target_y = predicted_y + randomness
            
            # Simular errores humanos con MISS_CHANCE
            if random.random() < settings['MISS_CHANCE']:
                target_y = random.random() * self.canvas_height
            
            self.ai_target_y = target_y
            
            # Mover la pala (similar a paddleUpdate en el original)
            paddle_center = paddle.y + (paddle.height / 2)
            dead_zone = 5  # Zona muerta para evitar oscilaciones
            
            if paddle_center < target_y - dead_zone:
                self.move_paddle('right', 1)
            elif paddle_center > target_y + dead_zone:
                self.move_paddle('right', -1)
            else:
                self.move_paddle('right', 0)

    def _predict_ball_y(self):
        """
        Predicción de la posición Y de la pelota, siguiendo la lógica del original
        """
        if self.ball.speed_x <= 0:
            return self.ball.y
            
        # Crear una copia de la pelota para simulación
        sim_ball = {
            'x': self.ball.x,
            'y': self.ball.y,
            'speed_x': self.ball.speed_x,
            'speed_y': self.ball.speed_y,
            'radius': self.ball.radius
        }
        
        # Simular trayectoria
        max_iterations = 500
        iterations = 0
        
        while sim_ball['x'] < self.paddles['right'].x and iterations < max_iterations:
            # Actualizar posición
            sim_ball['x'] += sim_ball['speed_x']
            sim_ball['y'] += sim_ball['speed_y']
            
            # Comprobar colisiones con bordes
            if sim_ball['y'] + sim_ball['radius'] >= self.canvas_height:
                sim_ball['y'] = self.canvas_height - sim_ball['radius']
                sim_ball['speed_y'] *= -1
            elif sim_ball['y'] - sim_ball['radius'] <= 0:
                sim_ball['y'] = self.ball.radius
                sim_ball['speed_y'] *= -1
                
            iterations += 1
            
        if iterations == max_iterations:
            print("Warning: predictBallY reached maximum iterations")
            return self.canvas_height / 2
            
        # Añadir margen de error como en el original
        error_margin = 15
        random_error = (random.random() * 2 * error_margin) - error_margin
        predicted_y = sim_ball['y'] + random_error
        
        # Asegurar que la predicción está dentro de los límites
        predicted_y = max(self.ball.radius, min(self.canvas_height - self.ball.radius, predicted_y))
        
        return predicted_y