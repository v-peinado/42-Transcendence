from .entities.ball import Ball
from .entities.paddle import Paddle
from .ai_controller import AIController

class GameState:

    def __init__(self, canvas_width=800, canvas_height=400):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Inicializar pelota y paletas
        self.ball = Ball(canvas_width/2, canvas_height/2, speed_x=0, speed_y=0)  # Inicializar sin velocidad
        paddle_height = 100
        self.paddles = {
            'left': Paddle(x=10, y=(canvas_height - paddle_height) / 2, height=paddle_height),
            'right': Paddle(x=canvas_width - 20, y=(canvas_height - paddle_height) / 2, height=paddle_height)
        }
        
        # Estado del juego
        self.status = 'waiting'
        self.countdown = 3
        self.countdown_active = False
        self.is_single_player = False
        self.difficulty = None  # Inicializar sin dificultad por defecto
        self.ai_controller = None

    def set_single_player(self, is_single, difficulty='medium'):
        """
        Configura el modo single player con una dificultad específica
        """
        self.is_single_player = is_single
        if is_single:
            self.difficulty = difficulty
            self.ai_controller = AIController(self)
            # Aplicar configuración inicial de dificultad
            self.ai_controller.apply_difficulty_settings(difficulty)
            # Inicializar velocidad de la bola según dificultad
            self._apply_difficulty_speed()
        else:
            self.difficulty = None
            self.ai_controller = None
            # Resetear velocidad de la bola a valores por defecto para multiplayer
            self.ball.speed_x = 2
            self.ball.speed_y = 2

    def _apply_difficulty_speed(self):
        """Aplica la velocidad de la bola según la dificultad actual"""
        if self.is_single_player and self.ai_controller:
            settings = self.ai_controller.DIFFICULTY_SETTINGS[self.difficulty]
            direction = 1 if self.ball.speed_x >= 0 else -1
            self.ball.speed_x = settings['BALL_SPEED'] * direction
            self.ball.speed_y = settings['BALL_SPEED']

    def update(self, timestamp=None):
        if self.countdown_active or self.status != 'playing':
            return

        self.ball.update(self.canvas_width, self.canvas_height)
        
        # Actualizar IA si es modo single player
        if self.is_single_player and self.ai_controller and timestamp:
            self.ai_controller.update(timestamp)
            
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
        """Reset la bola con la velocidad correspondiente a la dificultad actual"""
        self.ball.reset(self.canvas_width/2, self.canvas_height/2)
        if self.is_single_player and self.ai_controller:
            settings = self.ai_controller.DIFFICULTY_SETTINGS[self.difficulty]
            self.ball.speed_x = settings['BALL_SPEED'] * (-1 if scoring_side == 'right' else 1)
            self.ball.speed_y = settings['BALL_SPEED']
        
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
                side: paddle.serialize() for side, paddle in self.paddles.items()
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

    def start_countdown(self):
        self.countdown = 3
        self.countdown_active = True
        self.status = 'countdown'