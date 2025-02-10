import random
import math

class ScoreManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_scoring(self):
        """Comprueba si algún jugador ha marcado punto"""
        ball = self.game_state.ball
        
        # Comprobar si la pelota ha salido por los laterales
        if ball.x + ball.radius >= self.game_state.CANVAS_WIDTH:
            # Punto para el jugador izquierdo
            self.game_state.paddles['left'].score += 1
            print(f"Point scored by left player: {self.game_state.paddles['left'].score}")
            
            if self.game_state.paddles['left'].score >= self.game_state.WINNING_SCORE:
                return 'left'
            
            self._reset_ball('left')
            return None
            
        elif ball.x - ball.radius <= 0:
            # Punto para el jugador derecho
            self.game_state.paddles['right'].score += 1
            print(f"Point scored by right player: {self.game_state.paddles['right'].score}")
            
            if self.game_state.paddles['right'].score >= self.game_state.WINNING_SCORE:
                return 'right'
            
            self._reset_ball('right')
            return None
        
        return None

    def _reset_ball(self, scoring_side):
        """Reset la pelota después de un punto"""
        self.game_state.ball.x = self.game_state.CANVAS_WIDTH / 2
        self.game_state.ball.y = self.game_state.CANVAS_HEIGHT / 2
        
        # Dirección inicial hacia el jugador que perdió el punto
        direction = 1 if scoring_side == 'left' else -1
        angle = random.uniform(-0.5, 0.5)
        
        self.game_state.ball.speed_x = self.game_state.BALL_SPEED * direction
        self.game_state.ball.speed_y = self.game_state.BALL_SPEED * math.sin(angle)
        
        print(f"Ball reset after point - pos:({self.game_state.ball.x}, {self.game_state.ball.y}), speed:({self.game_state.ball.speed_x}, {self.game_state.ball.speed_y})")
