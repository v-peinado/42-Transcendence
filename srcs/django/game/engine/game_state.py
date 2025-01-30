from .entities.ball import Ball
from .entities.paddle import Paddle

class GameState:
    def __init__(self, canvas_width=800, canvas_height=400):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Inicializar pelota en el centro
        self.ball = Ball(canvas_width/2, canvas_height/2)
        
        # Inicializar paletas
        self.paddles = {
            'left': Paddle(
                x=10,
                y=canvas_height/2 - 50
            ),
            'right': Paddle(
                x=canvas_width - 20,
                y=canvas_height/2 - 50
            )
        }
        
        self.status = 'waiting'
        
    def update(self):
        if self.status != 'playing':
            return
            
        # Actualizar pelota
        self.ball.update(self.canvas_width, self.canvas_height)
        self._check_paddle_collisions()
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
            if direction != 0:
                new_y = paddle.y + (paddle.speed * direction)
                # Mantener la paleta dentro del canvas
                paddle.y = max(0, min(new_y, self.canvas_height - paddle.height))
                print(f"Paddle {side} moved to y={paddle.y}")  # Debug

    def serialize(self):
        return {
            'ball': self.ball.serialize(),
            'paddles': {
                side: paddle.serialize()
                for side, paddle in self.paddles.items()
            },
            'status': self.status,
            'canvas': {
                'width': self.canvas_width,
                'height': self.canvas_height
            }
        }