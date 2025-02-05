from math import sin as angle_sin

class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        base_speed = (
            self.game_state.ai_controller.DIFFICULTY_SETTINGS[self.game_state.difficulty]['BALL_SPEED']
            if self.game_state.is_single_player and self.game_state.ai_controller
            else self.game_state.MULTIPLAYER_SPEED
        )

        self._check_left_paddle_collision(base_speed)
        self._check_right_paddle_collision(base_speed)

    def _check_left_paddle_collision(self, base_speed):
        left_paddle = self.game_state.paddles['left']
        ball = self.game_state.ball
        
        ball_left_edge = ball.x - ball.radius
        ball_right_edge = ball.x + ball.radius
        paddle_right_edge = left_paddle.x + left_paddle.width

        if (ball_left_edge <= paddle_right_edge and
            ball_right_edge > left_paddle.x and
            ball.speed_x < 0 and
            ball.y > left_paddle.y and
            ball.y < left_paddle.y + left_paddle.height and
            ball_left_edge > left_paddle.x):
            
            ball.x = paddle_right_edge + ball.radius
            relative_intersect_y = (ball.y - (left_paddle.y + left_paddle.height/2)) / (left_paddle.height/2)
            angle = relative_intersect_y * 0.785398
            
            ball.speed_x = base_speed
            ball.speed_y = base_speed * angle_sin(angle)

    def _check_right_paddle_collision(self, base_speed):
        right_paddle = self.game_state.paddles['right']
        ball = self.game_state.ball
        
        ball_left_edge = ball.x - ball.radius
        ball_right_edge = ball.x + ball.radius
        paddle_left_edge = right_paddle.x

        if (ball_right_edge >= paddle_left_edge and
            ball_left_edge < right_paddle.x + right_paddle.width and
            ball.speed_x > 0 and
            ball.y > right_paddle.y and
            ball.y < right_paddle.y + right_paddle.height and
            ball_right_edge < right_paddle.x + right_paddle.width):
            
            ball.x = paddle_left_edge - ball.radius
            relative_intersect_y = (ball.y - (right_paddle.y + right_paddle.height/2)) / (right_paddle.height/2)
            angle = relative_intersect_y * 0.785398
            
            ball.speed_x = -base_speed
            ball.speed_y = base_speed * angle_sin(angle)
