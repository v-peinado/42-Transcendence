import random
import math

class ScoreManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_scoring(self):
        """Chequear si se ha marcado un punto"""
        ball = self.game_state.ball
        
        if ball.x + ball.radius >= self.game_state.CANVAS_WIDTH:									# Si la pelota ha salido por la derecha (todo el canvas)...
            self.game_state.paddles['left'].score += 1												# Punto para el jugador izquierdo (1)
            #print(f"Point scored by left player: {self.game_state.paddles['left'].score}")
            
            if self.game_state.paddles['left'].score >= self.game_state.WINNING_SCORE:				# Si el jugador izquierdo ha alcanzado el puntaje de victoria...
                return 'left'																		# Retornamos 'left' (el jugador izquierdo ha ganado)
            
            self._reset_ball('left')																# Reiniciar la pelota
            return None																				# Retornamos None (no hay ganador)
            
        elif ball.x - ball.radius <= 0:																# Si la pelota ha salido por la izquierda (no hay distancia de canvas)...
            self.game_state.paddles['right'].score += 1												# Punto para el jugador derecho (1)
            #print(f"Point scored by right player: {self.game_state.paddles['right'].score}")
            
            if self.game_state.paddles['right'].score >= self.game_state.WINNING_SCORE:				# Si el jugador derecho ha alcanzado el puntaje de victoria...
                return 'right'
            
            self._reset_ball('right')
            return None
        
        return None

    def _reset_ball(self, scoring_side):
        """Reset la pelota después de un punto"""
        self.game_state.ball.x = self.game_state.CANVAS_WIDTH / 2									# Ponemos la pelota en el centro del canvas
        self.game_state.ball.y = self.game_state.CANVAS_HEIGHT / 2									
        
        direction = 1 if scoring_side == 'left' else -1												# Seteamos las dirección de la pelota al sacar después de que se ha anotado un punto (1 si el jugador izquierdo ha marcado, -1 si el derecho)
        angle = random.uniform(-0.5, 0.5)
        
        self.game_state.ball.speed_x = self.game_state.BALL_SPEED * direction						# Seteamos la velocidad de la pelota al sacar después de que se ha anotado un punto
        self.game_state.ball.speed_y = self.game_state.BALL_SPEED * math.sin(angle)
        
        # print(f"Ball reset after point - pos:({self.game_state.ball.x}, {self.game_state.ball.y}), speed:({self.game_state.ball.speed_x}, {self.game_state.ball.speed_y})")
