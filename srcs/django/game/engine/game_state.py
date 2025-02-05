import math
import random
from math import sin as angle_sin
from .entities.ball import Ball
from .entities.paddle import Paddle
from .ai_controller import AIController

class GameState:
    WINNING_SCORE = 10  # Puntuación necesaria para ganar
    # Ajustar la velocidad multiplayer para que coincida con la dificultad media
    MULTIPLAYER_SPEED = 4

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
            # Inicializar con velocidad constante para multiplayer
            self.ball.speed_x = self.MULTIPLAYER_SPEED
            self.ball.speed_y = 0  # Comenzar con movimiento horizontal

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
            
        self._check_paddle_collisions()
        return self._check_scoring()  # Retornar el ganador si existe

    def _check_paddle_collisions(self):
        """
        Verificar colisiones con las paletas usando el borde de la pelota en lugar del centro.
        La colisión solo ocurre si el borde de la pelota no ha sobrepasado la línea de la pala.
        """
        base_speed = (
            self.ai_controller.DIFFICULTY_SETTINGS[self.difficulty]['BALL_SPEED']
            if self.is_single_player and self.ai_controller
            else self.MULTIPLAYER_SPEED
        )

        # Colisión con paleta izquierda
        left_paddle = self.paddles['left']
        ball_left_edge = self.ball.x - self.ball.radius
        ball_right_edge = self.ball.x + self.ball.radius
        paddle_right_edge = left_paddle.x + left_paddle.width

        if (ball_left_edge <= paddle_right_edge and                     			# El borde izquierdo de la pelota toca o cruza el borde derecho de la pala
            ball_right_edge > left_paddle.x and                         			# El borde derecho de la pelota no ha pasado completamente la pala
            self.ball.speed_x < 0 and                                 				# La pelota va hacia la izquierda
            self.ball.y > left_paddle.y and 
            self.ball.y < left_paddle.y + left_paddle.height and
            ball_left_edge > left_paddle.x):                           				# El borde izquierdo de la pelota no ha pasado el borde izquierdo de la pala
            
            # Colocar la pelota justo en el punto de colisión
            self.ball.x = paddle_right_edge + self.ball.radius
            relative_intersect_y = (self.ball.y - (left_paddle.y + left_paddle.height/2)) / (left_paddle.height/2)
            angle = relative_intersect_y * 0.785398
            
            self.ball.speed_x = base_speed
            self.ball.speed_y = base_speed * angle_sin(angle)
            
        # Colisión con paleta derecha
        right_paddle = self.paddles['right']
        paddle_left_edge = right_paddle.x

        if (ball_right_edge >= paddle_left_edge and                    				# El borde derecho de la pelota toca o cruza el borde izquierdo de la pala
            ball_left_edge < right_paddle.x + right_paddle.width and   				# El borde izquierdo de la pelota no ha pasado completamente la pala
            self.ball.speed_x > 0 and                                  				# La pelota va hacia la derecha
            self.ball.y > right_paddle.y and 
            self.ball.y < right_paddle.y + right_paddle.height and
            ball_right_edge < right_paddle.x + right_paddle.width):   				# El borde derecho de la pelota no ha pasado el borde derecho de la pala
            
            # Colocar la pelota justo en el punto de colisión
            self.ball.x = paddle_left_edge - self.ball.radius
            relative_intersect_y = (self.ball.y - (right_paddle.y + right_paddle.height/2)) / (right_paddle.height/2)
            angle = relative_intersect_y * 0.785398
            
            self.ball.speed_x = -base_speed
            self.ball.speed_y = base_speed * angle_sin(angle)

    def _check_scoring(self):
        """
        Verificar si se ha anotado un punto y si alguien ha ganado.
        """
        winner = None

        # Punto para jugador derecho
        if self.ball.x + self.ball.radius < 0:
            self.paddles['right'].score += 1
            if self.paddles['right'].score >= self.WINNING_SCORE:
                self.status = 'finished'
                winner = 'right'
            self._reset_ball('right')
            
        # Punto para jugador izquierdo
        elif self.ball.x - self.ball.radius > self.canvas_width:
            self.paddles['left'].score += 1
            if self.paddles['left'].score >= self.WINNING_SCORE:
                self.status = 'finished'
                winner = 'left'
            self._reset_ball('left')

        return winner

    def _reset_ball(self, scoring_side):
        """Reset la bola con la velocidad correspondiente a la dificultad actual"""
        self.ball.reset(self.canvas_width/2, self.canvas_height/2)
        if self.is_single_player and self.ai_controller:
            settings = self.ai_controller.DIFFICULTY_SETTINGS[self.difficulty]
            base_speed = settings['BALL_SPEED']
            
            # Usar un ángulo aleatorio entre -30 y 30 grados
            angle = random.uniform(-0.523599, 0.523599)  # ±π/6 radianes = ±30 grados
            
            # Calcular componentes manteniendo velocidad total constante
            self.ball.speed_x = base_speed * (-1 if scoring_side == 'right' else 1) * abs(math.cos(angle))
            self.ball.speed_y = base_speed * math.sin(angle)
        else:
            # Reset para modo multiplayer
            angle = random.uniform(-0.5, 0.5)  # Ángulo más suave para multiplayer
            self.ball.speed_x = self.MULTIPLAYER_SPEED * (-1 if scoring_side == 'right' else 1)
            self.ball.speed_y = self.MULTIPLAYER_SPEED * angle_sin(angle)
        
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