from .components.collision_manager import CollisionManager
from .components.score_manager import ScoreManager
from .entities.ball import Ball
from .entities.paddle import Paddle

class GameState:
    CANVAS_WIDTH = 1000
    CANVAS_HEIGHT = 600
    WINNING_SCORE = 10
    PLAYER_SPEED = 7
    BALL_SPEED = 7
    PADDLE_WIDTH = 10
    PADDLE_HEIGHT = 160

    def __init__(self):
        """Seteo del estado inicial del juego"""
        self.ball = Ball(self.CANVAS_WIDTH/2, self.CANVAS_HEIGHT/2)
        
        paddle_y = (self.CANVAS_HEIGHT - self.PADDLE_HEIGHT) / 2
        self.paddles = {
            'left': Paddle(
                x=10,													# 10 píxeles de separación del borde izquierdo
                y=paddle_y,
                width=self.PADDLE_WIDTH,
                height=self.PADDLE_HEIGHT
            ),
            'right': Paddle(
                x=self.CANVAS_WIDTH - 20,								# 10 píxeles de separación del borde derecho
                y=paddle_y,
                width=self.PADDLE_WIDTH,
                height=self.PADDLE_HEIGHT
            )
        }
        
        self.status = 'waiting'											# Estado inicial del juego
        self.countdown = 3
        self.countdown_active = False
        
        self.collision_manager = CollisionManager(self)					# Inicializar el gestor de colisiones
        self.score_manager = ScoreManager(self)							# Inicializar el gestor de puntuación

    def update(self, timestamp=None):
        """Actualiza el estado del juego"""
        if self.status != 'playing':
            return None

        self.ball.update(self.CANVAS_WIDTH, self.CANVAS_HEIGHT)			# Actualizar la posición de la pelota
        
        self.collision_manager.check_collisions()						# Comprobar colisiones con las palas
        
        winner = self.score_manager.check_scoring()						# Comprobar si hay un ganador
        if winner:
            # print(f"Winner detected: {winner} - Scores: {self.paddles['left'].score}-{self.paddles['right'].score}")
            self.status = 'finished'
            return winner
        
        return None

    def move_paddle(self, side, direction):								# Mover la pala
        """Movimiento de la pala"""
        if side in self.paddles:
            paddle = self.paddles[side]
            move_amount = self.PLAYER_SPEED * direction
            new_y = paddle.y + move_amount
            
            # Para que la pala no se salga de los límites...
            paddle.y = max(0, min(new_y, self.CANVAS_HEIGHT - self.PADDLE_HEIGHT))

    async def start_countdown(self):
        """Inicia la cuenta atrás para el inicio del juego"""
        self.countdown = 3
        self.countdown_active = True
        self.status = 'countdown'
        
        # para asegurar que la pelota comienza con velocidad
        self.ball.reset(
            x=self.CANVAS_WIDTH / 2,
            y=self.CANVAS_HEIGHT / 2,
        )
        # print(f"Ball position reset to: ({self.ball.x}, {self.ball.y})")  # Debug

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
                'width': self.CANVAS_WIDTH,
                'height': self.CANVAS_HEIGHT
            }
        }
        
        if self.countdown_active:
            current_state['countdown'] = self.countdown
            
        return current_state