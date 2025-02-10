import random
import math
from math import sin as angle_sin

class ScoreManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_scoring(self):
        """Comprueba si algún jugador ha marcado punto y determina el ganador"""
        if self._check_right_score():
            self.game_state.paddles['right'].score += 1
            print(f"Right scored: {self.game_state.paddles['right'].score}")  # Debug log
            
            if self.game_state.paddles['right'].score >= self.game_state.WINNING_SCORE:
                self.game_state.status = 'finished'
                return 'right'
                
            self.reset_ball('right')
            
        elif self._check_left_score():
            self.game_state.paddles['left'].score += 1
            print(f"Left scored: {self.game_state.paddles['left'].score}")  # Debug log
            
            if self.game_state.paddles['left'].score >= self.game_state.WINNING_SCORE:
                self.game_state.status = 'finished'
                return 'left'
                
            self.reset_ball('left')

        return None

    def _check_left_score(self):
        return self.game_state.ball.x - self.game_state.ball.radius > self.game_state.canvas_width

    def _check_right_score(self):
        return self.game_state.ball.x + self.game_state.ball.radius < 0

    def reset_ball(self, scoring_side):
        self.game_state.ball.reset(self.game_state.canvas_width/2, self.game_state.canvas_height/2)
        angle = random.uniform(-0.5, 0.5)
        self.game_state.ball.speed_x = self.game_state.GAME_SPEED * (-1 if scoring_side == 'right' else 1)
        self.game_state.ball.speed_y = self.game_state.GAME_SPEED * angle_sin(angle)

    def _reset_single_player(self, scoring_side):
        settings = self.game_state.ai_controller.DIFFICULTY_SETTINGS[self.game_state.difficulty]
        base_speed = settings['BALL_SPEED']
        
        # Usar un ángulo aleatorio entre -30 y 30 grados
        angle = random.uniform(-0.523599, 0.523599)  # ±π/6 radianes
        
        # Calcular componentes manteniendo velocidad total constante
        self.game_state.ball.speed_x = base_speed * (-1 if scoring_side == 'right' else 1) * abs(math.cos(angle))
        self.game_state.ball.speed_y = base_speed * math.sin(angle)

    def _reset_multiplayer(self, scoring_side):
        angle = random.uniform(-0.5, 0.5)  # Ángulo más suave para multiplayer
        self.game_state.ball.speed_x = self.game_state.MULTIPLAYER_SPEED * (-1 if scoring_side == 'right' else 1)
        self.game_state.ball.speed_y = self.game_state.MULTIPLAYER_SPEED * angle_sin(angle)
