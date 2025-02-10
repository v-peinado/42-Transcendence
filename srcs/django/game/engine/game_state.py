from .components.collision_manager import CollisionManager
from .components.score_manager import ScoreManager
from .entities.ball import Ball
from .entities.paddle import Paddle

class GameState:
    WINNING_SCORE = 10
    GAME_SPEED = 4

    def __init__(self, canvas_width=800, canvas_height=400):
        """Inicialización del estado del juego"""
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        self.ball = Ball(canvas_width/2, canvas_height/2, speed_x=0, speed_y=0)
        paddle_height = 100
        self.paddles = {
            'left': Paddle(x=10, y=(canvas_height - paddle_height) / 2, height=paddle_height),
            'right': Paddle(x=canvas_width - 20, y=(canvas_height - paddle_height) / 2, height=paddle_height)
        }
        
        self.status = 'waiting'
        self.countdown = 3
        self.countdown_active = False
        
        self.collision_manager = CollisionManager(self)
        self.score_manager = ScoreManager(self)

    def update(self, timestamp=None):
        """Actualiza el estado del juego"""
        if self.status != 'playing':
            return None

        # Actualizar posición de la pelota
        self.ball.x += self.ball.speed_x
        self.ball.y += self.ball.speed_y

        # Comprobar colisiones con paredes superior e inferior
        if self.ball.y + self.ball.radius > self.canvas_height:
            self.ball.y = self.canvas_height - self.ball.radius
            self.ball.speed_y *= -1
        elif self.ball.y - self.ball.radius < 0:
            self.ball.y = self.ball.radius
            self.ball.speed_y *= -1

        # Comprobar colisiones con paletas
        self.collision_manager.check_collisions()
        return self.score_manager.check_scoring()

    def move_paddle(self, side, direction):
        """
        Mueve una paleta en una dirección
        side: 'left' o 'right'
        direction: -1 (arriba), 0 (parar), 1 (abajo)
        """
        if side in self.paddles:
            paddle = self.paddles[side]
            paddle_speed = 5  # Velocidad de movimiento de las palas
            paddle.y += direction * paddle_speed
            
            # Limitar el movimiento al canvas
            paddle.y = max(0, min(paddle.y, self.canvas_height - paddle.height))

    async def start_countdown(self):
        """Inicia la cuenta atrás para el inicio del juego"""
        self.countdown = 3
        self.countdown_active = True
        self.status = 'countdown'
        # Resetear posición y velocidad de la pelota
        self.ball.x = self.canvas_width / 2
        self.ball.y = self.canvas_height / 2
        self.ball.speed_x = self.GAME_SPEED
        self.ball.speed_y = 0

    def serialize(self):
        """Serialización del estado del juego"""
        current_state = {
            'ball': self.ball.serialize() if hasattr(self.ball, 'serialize') else {
                'x': self.ball.x,
                'y': self.ball.y,
                'radius': self.ball.radius,
                'speed_x': self.ball.speed_x,
                'speed_y': self.ball.speed_y
            },
            'paddles': {
                side: {
                    'x': paddle.x,
                    'y': paddle.y,
                    'width': paddle.width,
                    'height': paddle.height,
                    'score': getattr(paddle, 'score', 0)
                } for side, paddle in self.paddles.items()
            },
            'status': self.status,
            'canvas': {
                'width': self.canvas_width,
                'height': self.canvas_height
            }
        }
        
        if self.countdown_active:
            current_state['countdown'] = self.countdown
            
        return current_state