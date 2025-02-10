import math
from math import sin as angle_sin

class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        """Sistema de colisiones mejorado"""
        ball = self.game_state.ball
        
        # Establecer límites del canvas
        if ball.x + ball.radius > self.game_state.CANVAS_WIDTH:
            ball.x = self.game_state.CANVAS_WIDTH - ball.radius
            ball.speed_x *= -1
        elif ball.x - ball.radius < 0:
            ball.x = ball.radius
            ball.speed_x *= -1

        # Comprobar colisiones con paletas
        for side, paddle in self.game_state.paddles.items():
            # Calcular distancias
            dx = abs(ball.x - paddle.x)
            dy = abs(ball.y - (paddle.y + paddle.height/2))
            
            # Verificar colisión
            if (dx < (ball.radius + paddle.width) and 
                ball.y >= paddle.y and 
                ball.y <= paddle.y + paddle.height):
                
                # Calcular ángulo de rebote
                relative_intersect_y = (ball.y - (paddle.y + paddle.height/2))
                normalized_intersect = relative_intersect_y / (paddle.height/2)
                angle = normalized_intersect * 0.75
                
                # Invertir dirección y aplicar ángulo
                if side == 'left' and ball.speed_x < 0:
                    ball.speed_x = self.game_state.BALL_SPEED
                    ball.speed_y = self.game_state.BALL_SPEED * math.sin(angle)
                    ball.x = paddle.x + paddle.width + ball.radius
                elif side == 'right' and ball.speed_x > 0:
                    ball.speed_x = -self.game_state.BALL_SPEED
                    ball.speed_y = self.game_state.BALL_SPEED * math.sin(angle)
                    ball.x = paddle.x - ball.radius

                print(f"Collision with {side} paddle at y={ball.y}, new speed=({ball.speed_x}, {ball.speed_y})")
