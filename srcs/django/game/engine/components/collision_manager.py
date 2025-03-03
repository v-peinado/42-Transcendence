import math


class CollisionManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def check_collisions(self):
        """Combina la detección de colisiones y el cálculo del ángulo de rebote."""
        ball = self.game_state.ball

        for side, paddle in self.game_state.paddles.items():
            # Calcular la distancia del centro de la pelota al centro de la pala
            dx = abs(ball.x - (paddle.x + paddle.width / 2))
            dy = abs(ball.y - (paddle.y + paddle.height / 2))

            # Si se detecta colisión
            if dx <= (ball.radius + paddle.width / 2) and dy <= (ball.radius + paddle.height / 2):
                if dx > paddle.width / 2:
                    # Colisión en los laterales: usar el cálculo de ángulo de rebote
                    relative_intersect_y = ball.y - (paddle.y + paddle.height / 2)
                    normalized_intersect = relative_intersect_y / (paddle.height / 2)
                    bounce_angle = normalized_intersect * (math.pi / 4)  # máximo 45 grados

                    if side == "left" and ball.speed_x < 0:
                        ball.speed_x = self.game_state.BALL_SPEED * math.cos(bounce_angle)
                        ball.speed_y = self.game_state.BALL_SPEED * math.sin(bounce_angle)
                        ball.x = paddle.x + paddle.width + ball.radius
                    elif side == "right" and ball.speed_x > 0:
                        ball.speed_x = -self.game_state.BALL_SPEED * math.cos(bounce_angle)
                        ball.speed_y = self.game_state.BALL_SPEED * math.sin(bounce_angle)
                        ball.x = paddle.x - ball.radius

                elif dy > paddle.height / 2:
                    # Colisión en la parte superior o inferior: invertir velocidad vertical
                    ball.speed_y *= -1
                    if ball.y < paddle.y:
                        ball.y = paddle.y - ball.radius
                    else:
                        ball.y = paddle.y + paddle.height + ball.radius

                else:
                    # Colisión en la esquina: invertir ambas velocidades
                    ball.speed_x *= -1
                    ball.speed_y *= -1
                    # Ajustar la posición para evitar que la pelota se quede atascada
                    if ball.x < paddle.x:
                        ball.x = paddle.x - ball.radius
                    else:
                        ball.x = paddle.x + paddle.width + ball.radius
                    if ball.y < paddle.y:
                        ball.y = paddle.y - ball.radius
                    else:
                        ball.y = paddle.y + paddle.height + ball.radius
