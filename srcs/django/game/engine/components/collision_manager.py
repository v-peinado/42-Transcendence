import math
import random

class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        """Check for collisions between ball and paddles"""
        ball = self.game_state.ball

        for side, paddle in self.game_state.paddles.items():
            # Calculating distance between ball and paddle
            dx = abs(ball.x - (paddle.x + paddle.width / 2))
            dy = abs(ball.y - (paddle.y + paddle.height / 2))

            # If distance is less than the sum of the radii, there's a collision
            if dx <= (ball.radius + paddle.width / 2) and dy <= (ball.radius + paddle.height / 2):
                # Determine which side of the paddle was hit
                is_front_collision = (side == "left" and ball.speed_x < 0) or (side == "right" and ball.speed_x > 0)
                
                if is_front_collision and abs(ball.y - (paddle.y + paddle.height / 2)) < paddle.height / 2:
                    # Collision on the front side: calculate bounce angle
                    relative_intersect_y = ball.y - (paddle.y + paddle.height / 2)
                    normalized_intersect = relative_intersect_y / (paddle.height / 2)
                    bounce_angle = normalized_intersect * (math.pi / 4) + random.uniform(-0.05, 0.05) # max bounce angle = 45 degrees

                    # Update ball speed and position
                    speed = ball.base_speed
                    
                    if side == "left":
                        ball.speed_x = speed * math.cos(bounce_angle)
                        ball.speed_y = speed * math.sin(bounce_angle)
                        ball.x = paddle.x + paddle.width + ball.radius + 1  # +1 to avoid sticking
                    else:  # right
                        ball.speed_x = -speed * math.cos(bounce_angle)
                        ball.speed_y = speed * math.sin(bounce_angle)
                        ball.x = paddle.x - ball.radius - 1  # -1 to avoid sticking
                
                elif dy > paddle.height / 2:
                    # Collision on the top or bottom side: invert vertical speed
                    ball.speed_y *= -1
                    if ball.y < paddle.y:
                        ball.y = paddle.y - ball.radius - 1
                    else:
                        ball.y = paddle.y + paddle.height + ball.radius + 1
                
                else:
                    # Collision on the sides: invert horizontal speed
                    ball.speed_x *= -1
                    
                    # Adjust ball position to avoid sticking
                    if side == "left":
                        ball.x = paddle.x + paddle.width + ball.radius + 1
                    else:
                        ball.x = paddle.x - ball.radius - 1
                
                # Ensure constant speed
                total_speed = math.sqrt(ball.speed_x**2 + ball.speed_y**2)
                if abs(total_speed - ball.base_speed) > 0.1:
                    scale = ball.base_speed / total_speed
                    ball.speed_x *= scale
                    ball.speed_y *= scale
                
                # Once collision is detected, exit loop
                break
