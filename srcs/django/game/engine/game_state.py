from .components.collision_manager import CollisionManager
from .components.score_manager import ScoreManager
from .components.game_mode_manager import GameModeManager
from .entities.ball import Ball
from .entities.paddle import Paddle
from .ai_controller import AIController

class GameState:
    WINNING_SCORE = 10
    MULTIPLAYER_SPEED = 4															# Velocidad multiplayer coincidente con la de la dificultad 'medium' de la IA

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
        
        # Managers
        self.collision_manager = CollisionManager(self)
        self.score_manager = ScoreManager(self)
        self.mode_manager = GameModeManager(self)

    def set_single_player(self, is_single, difficulty='medium'):
        """Delegamos la configuración del modo de juego al GameModeManager"""
        self.mode_manager.set_single_player(is_single, difficulty)

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
            return None

        self.ball.update(self.canvas_width, self.canvas_height)
        
        if self.is_single_player and self.ai_controller and timestamp:				# Actualización del controlador de la IA
            self.ai_controller.update(timestamp)
            
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