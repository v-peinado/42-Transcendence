import math


class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        """Check collisions with paddles and calculate bounce angles"""
        ball = self.game_state.ball

        for side, paddle in self.game_state.paddles.items():
            # Calculate distance to paddle center
            dx = abs(ball.x - (paddle.x + paddle.width / 2))							# Calculate x distance
            dy = abs(ball.y - (paddle.y + paddle.height / 2))							# Calculate y distance

            # Check collision by distance to paddle center
            if dx <= (ball.radius + paddle.width / 2) and dy <= (
                ball.radius + paddle.height / 2
            ):																			# Check x and y collision

                # Calculate relative impact point on paddle
                relative_intersect_y = ball.y - (paddle.y + paddle.height / 2)
                normalized_intersect = relative_intersect_y / (paddle.height / 2)
                bounce_angle = normalized_intersect * (
                    math.pi / 4
                )  # Maximum 45 degrees

                # Apply bounce angle based on ball impact point against paddle
                if side == "left" and ball.speed_x < 0:
                    ball.speed_x = self.game_state.BALL_SPEED * math.cos(bounce_angle)
                    ball.speed_y = self.game_state.BALL_SPEED * math.sin(bounce_angle)
                    ball.x = paddle.x + paddle.width + ball.radius
                elif side == "right" and ball.speed_x > 0:
                    ball.speed_x = -self.game_state.BALL_SPEED * math.cos(bounce_angle)
                    ball.speed_y = self.game_state.BALL_SPEED * math.sin(bounce_angle)
                    ball.x = paddle.x - ball.radius
