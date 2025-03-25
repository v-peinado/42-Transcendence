import random
import math


class ScoreManager:
    def __init__(self, game_state):
        """Initialize ScoreManager with game state"""
        self.game_state = game_state

    def check_scoring(self):
        """Check if a point has been scored"""
        ball = self.game_state.ball # Get ball object

        if (
            ball.x + ball.radius >= self.game_state.CANVAS_WIDTH
        ):  # If ball exits through right side...
            self.game_state.paddles["left"].score += 1  # Point for left player

            if (  # If left player has reached winning score...
                self.game_state.paddles["left"].score >= self.game_state.WINNING_SCORE
            ):
                return "left"  # Return left player as winner

            self._reset_ball("left")
            return None

        elif ball.x - ball.radius <= 0:  # If ball exits through left side...
            self.game_state.paddles["right"].score += 1  # Point for right player

            if (
                self.game_state.paddles["right"].score >= self.game_state.WINNING_SCORE
            ):  # etc...
                return "right"

            self._reset_ball("right")
            return None

        return None

    def _reset_ball(self, scoring_side):
        """Reset ball after scoring"""
        self.game_state.ball.x = (
            self.game_state.CANVAS_WIDTH / 2
        )  # Place ball at canvas center
        self.game_state.ball.y = self.game_state.CANVAS_HEIGHT / 2

        direction = (
            1 if scoring_side == "left" else -1
        )  # Set ball direction after scoring
        angle = random.uniform(-0.5, 0.5)

		# Set ball speed based on direction and angle
        self.game_state.ball.speed_x = self.game_state.BALL_SPEED * direction
        self.game_state.ball.speed_y = self.game_state.BALL_SPEED * math.sin(angle)
