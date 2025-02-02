from .entities.ball import Ball
from .entities.paddle import Paddle
from .ai_controller import AIController

class GameState:

    def __init__(self, canvas_width=800, canvas_height=400):
        """ Inicialización del estado del juego """
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Setear pelota y paletas
        self.ball = Ball(canvas_width/2, canvas_height/2, speed_x=0, speed_y=0)
        paddle_height = 100
        self.paddles = {
            'left': Paddle(x=10, y=(canvas_height - paddle_height) / 2, height=paddle_height),
            'right': Paddle(x=canvas_width - 20, y=(canvas_height - paddle_height) / 2, height=paddle_height)
        }
        
        # Setear estado inicial del juego
        self.status = 'waiting'
        self.countdown = 3
        self.countdown_active = False
        self.is_single_player = False
        self.difficulty = None
        self.ai_controller = None

    def set_single_player(self, is_single, difficulty='medium'):
        """ Configura la partida en modo single player o multiplayer """
        self.is_single_player = is_single
        if is_single:
            self.difficulty = difficulty
            self.ai_controller = AIController(self)
            self.ai_controller.apply_difficulty_settings(difficulty)
            self._apply_difficulty_speed()
        else:																		# Configuración de partida multijugador
            self.difficulty = None
            self.ai_controller = None
            self.ball.speed_x = 2
            self.ball.speed_y = 2

    def _apply_difficulty_speed(self):
        """ Aplicar la velocidad de la bola según la dificultad actual """
        if self.is_single_player and self.ai_controller:
            settings = self.ai_controller.DIFFICULTY_SETTINGS[self.difficulty]
            direction = 1 if self.ball.speed_x >= 0 else -1							# Dirección actual de la bola
            self.ball.speed_x = settings['BALL_SPEED'] * direction					# Velocidad de la bola
            self.ball.speed_y = settings['BALL_SPEED']	

    def update(self, timestamp=None):
        """ Actualización del estado del juego """
        if self.countdown_active or self.status != 'playing':
            return

        self.ball.update(self.canvas_width, self.canvas_height)
        
        if self.is_single_player and self.ai_controller and timestamp:				# Actualización del controlador de la IA
            self.ai_controller.update(timestamp)
            
        self._check_paddle_collisions()
        self._check_scoring()

    def _check_paddle_collisions(self):
        """ Verificar colisiones con las paletas """
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
        """ Verificar si se ha anotado un punto """
        if self.ball.x < 0:															# Punto para Player 2
            self.paddles['right'].score += 1
            self._reset_ball('right')
            
        elif self.ball.x > self.canvas_width:										# Punto para Player 1
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
            current_y = paddle.y  														# Guardar posición actual
            paddle.move(direction, self.canvas_height)
            print(f"GameState: paddle {side} moved from {current_y} to {paddle.y}")

    def serialize(self):
        """ Serialización del estado del juego """
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
        """ Inicia la cuenta atrás para el inicio del juego """
        self.countdown = 3
        self.countdown_active = True
        self.status = 'countdown'