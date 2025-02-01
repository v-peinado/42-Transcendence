from .entities.ball import Ball
from .entities.paddle import Paddle
import random

class GameState:
    DIFFICULTY_SETTINGS = {
        'easy': {'BALL_SPEED': 5, 'AI_REACTION_TIME': 300, 'ERROR_MARGIN': 60},
        'medium': {'BALL_SPEED': 7, 'AI_REACTION_TIME': 200, 'ERROR_MARGIN': 40},
        'hard': {'BALL_SPEED': 9, 'AI_REACTION_TIME': 100, 'ERROR_MARGIN': 20}
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
        
    def start_countdown(self):
        self.countdown = 3
        self.countdown_active = True
        self.status = 'countdown'
        
    def update(self):
        if self.countdown_active:
            return  # No actualizar la pelota durante el countdown

        if self.status != 'playing':
            return
            
        # Actualizar pelota
        self.ball.update(self.canvas_width, self.canvas_height)
        
        # IA para modo single player
        if self.is_single_player:
            self._update_ai()
            
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
        if self.status != 'playing':
            return
            
        settings = self.DIFFICULTY_SETTINGS[self.difficulty]
        paddle = self.paddles['right']
        ball = self.ball
        
        # Predicción de posición de la pelota
        predicted_y = self._predict_ball_y()
        
        # Añadir error según dificultad
        error = (random.random() * 2 - 1) * settings['ERROR_MARGIN']
        target_y = predicted_y + error
        
        # Mover la pala AI
        if paddle.y + (paddle.height / 2) < target_y - 5:
            self.move_paddle('right', 1)
        elif paddle.y + (paddle.height / 2) > target_y + 5:
            self.move_paddle('right', -1)
            
    def _predict_ball_y(self):
        """
        Predice la posición Y donde la pelota intersectará con la pala derecha
        Retorna: posición Y predicha
        """
        # Si la pelota va hacia la izquierda, retornar posición actual
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

        # Simular el movimiento de la pelota hasta que alcance la pala derecha
        max_iterations = 500  # Prevenir bucle infinito
        iterations = 0
        
        while sim_ball['x'] < self.paddles['right'].x and iterations < max_iterations:
            # Actualizar posición
            sim_ball['x'] += sim_ball['speed_x']
            sim_ball['y'] += sim_ball['speed_y']
            
            # Comprobar colisiones con bordes superior e inferior
            if sim_ball['y'] + sim_ball['radius'] >= self.canvas_height:
                sim_ball['y'] = self.canvas_height - sim_ball['radius']
                sim_ball['speed_y'] *= -1
            elif sim_ball['y'] - sim_ball['radius'] <= 0:
                sim_ball['y'] = sim_ball['radius']
                sim_ball['speed_y'] *= -1
                
            iterations += 1

        if iterations == max_iterations:
            print("Warning: _predict_ball_y reached maximum iterations")
            return self.canvas_height / 2  # Retornar posición central si no se puede predecir

        return sim_ball['y']