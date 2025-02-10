import math

class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        ball = self.game_state.ball
        
        for side, paddle in self.game_state.paddles.items():
            # Calcular distancia al centro de la pala
            dx = abs(ball.x - (paddle.x + paddle.width/2))
            dy = abs(ball.y - (paddle.y + paddle.height/2))
            
            # Verificar colisión precisa
            if (dx <= (ball.radius + paddle.width/2) and 
                dy <= (ball.radius + paddle.height/2)):
                
                # Calcular punto de impacto relativo
                relative_intersect_y = (ball.y - (paddle.y + paddle.height/2))
                normalized_intersect = relative_intersect_y / (paddle.height/2)
                bounce_angle = normalized_intersect * (math.pi/4)  # Máximo 45 grados
                
                # Aplicar rebote con velocidad constante
                if side == 'left' and ball.speed_x < 0:
                    ball.speed_x = self.game_state.BALL_SPEED * math.cos(bounce_angle)
                    ball.speed_y = self.game_state.BALL_SPEED * math.sin(bounce_angle)
                    ball.x = paddle.x + paddle.width + ball.radius
                elif side == 'right' and ball.speed_x > 0:
                    ball.speed_x = -self.game_state.BALL_SPEED * math.cos(bounce_angle)
                    ball.speed_y = self.game_state.BALL_SPEED * math.sin(bounce_angle)
                    ball.x = paddle.x - ball.radius

                print(f"Collision with {side} paddle - angle:{bounce_angle}, speed:({ball.speed_x}, {ball.speed_y})")
