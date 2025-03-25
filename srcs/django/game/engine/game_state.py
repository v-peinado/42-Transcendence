from .components.collision_manager import CollisionManager
from .components.score_manager import ScoreManager
from .entities.paddle import Paddle
from .entities.ball import Ball


class GameState:
    CANVAS_WIDTH = 1000
    CANVAS_HEIGHT = 600
    WINNING_SCORE = 10
    PLAYER_SPEED = 7
    BALL_SPEED = 9
    PADDLE_WIDTH = 10
    PADDLE_HEIGHT = 100

    def __init__(self):
        """Initial game state setup"""
        self.ball = Ball(
            self.CANVAS_WIDTH / 2, 
            self.CANVAS_HEIGHT / 2,
            base_speed=self.BALL_SPEED
        )

        paddle_y = (self.CANVAS_HEIGHT - self.PADDLE_HEIGHT) / 2
        self.paddles = {
            "left": Paddle(
                x=10,  # 10 pixels from left edge
                y=paddle_y,
                width=self.PADDLE_WIDTH,
                height=self.PADDLE_HEIGHT,
            ),
            "right": Paddle(
                x=self.CANVAS_WIDTH - 20,  # 10 pixels from right edge
                y=paddle_y,
                width=self.PADDLE_WIDTH,
                height=self.PADDLE_HEIGHT,
            ),
        }

        self.status = "waiting"  # Initial game status
        self.countdown = 3
        self.countdown_active = False

        self.collision_manager = CollisionManager(self)  # Initialize collision manager
        self.score_manager = ScoreManager(self)  # Initialize score manager

    def update(self, timestamp=None):
        """Updates the game state"""
        if self.status != "playing":
            return None

        self.ball.update(self.CANVAS_WIDTH, self.CANVAS_HEIGHT)  # Update ball position

        self.collision_manager.check_collisions()  # Check paddle collisions

        winner = self.score_manager.check_scoring()  # Check for winner
        if winner:
            self.status = "finished"
            return winner

        return None

    def move_paddle(self, side, direction):  # Move paddle
        """Paddle movement"""
        if side in self.paddles:
            paddle = self.paddles[side]
            move_amount = self.PLAYER_SPEED * direction
            new_y = paddle.y + move_amount

            # To keep paddle within canvas bounds...
            paddle.y = max(0, min(new_y, self.CANVAS_HEIGHT - self.PADDLE_HEIGHT))

    async def start_countdown(self):
        """Starts the countdown for game start"""
        self.countdown = 3
        self.countdown_active = True
        self.status = "countdown"

        # Ensure ball starts with velocity
        self.ball.reset(
            x=self.CANVAS_WIDTH / 2,
            y=self.CANVAS_HEIGHT / 2,
        )
        # print(f"Ball position reset to: ({self.ball.x}, {self.ball.y})")  # Debug

    def serialize(self):
        """Serializes the game state"""
        current_state = {
            "ball": (
                self.ball.serialize()
                if hasattr(self.ball, "serialize")
                else {
                    "x": self.ball.x,
                    "y": self.ball.y,
                    "radius": self.ball.radius,
                    "speed_x": self.ball.speed_x,
                    "speed_y": self.ball.speed_y,
                }
            ),
            "paddles": {
                side: {
                    "x": paddle.x,
                    "y": paddle.y,
                    "width": paddle.width,
                    "height": paddle.height,
                    "score": getattr(paddle, "score", 0),
                }
                for side, paddle in self.paddles.items()
            },
            "status": self.status,
            "canvas": {"width": self.CANVAS_WIDTH, "height": self.CANVAS_HEIGHT},
        }

        if self.countdown_active:
            current_state["countdown"] = self.countdown

        return current_state
