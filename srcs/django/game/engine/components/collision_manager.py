from math import sin as angle_sin

class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        """Comprueba colisiones con las paletas"""
        ball = self.game_state.ball
        base_speed = self.game_state.GAME_SPEED

        # Colisión con paleta izquierda
        left_paddle = self.game_state.paddles['left']
        if (ball.x - ball.radius <= left_paddle.x + left_paddle.width and
            ball.x + ball.radius >= left_paddle.x and
            ball.y >= left_paddle.y and
            ball.y <= left_paddle.y + left_paddle.height and
            ball.speed_x < 0):
            
            ball.x = left_paddle.x + left_paddle.width + ball.radius
            relative_intersect_y = (ball.y - (left_paddle.y + left_paddle.height/2)) / (left_paddle.height/2)
            angle = relative_intersect_y * 0.75
            ball.speed_x = base_speed
            ball.speed_y = base_speed * angle_sin(angle)

        # Colisión con paleta derecha
        right_paddle = self.game_state.paddles['right']
        if (ball.x + ball.radius >= right_paddle.x and
            ball.x - ball.radius <= right_paddle.x + right_paddle.width and
            ball.y >= right_paddle.y and
            ball.y <= right_paddle.y + right_paddle.height and
            ball.speed_x > 0):
            
            ball.x = right_paddle.x - ball.radius
            relative_intersect_y = (ball.y - (right_paddle.y + right_paddle.height/2)) / (right_paddle.height/2)
            angle = relative_intersect_y * 0.75
            ball.speed_x = -base_speed
            ball.speed_y = base_speed * angle_sin(angle)
