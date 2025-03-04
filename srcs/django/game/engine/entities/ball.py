import random
import math


class Ball:
    def __init__(self, x, y, radius=10, base_speed=7):  
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = base_speed

    def update(self, canvas_width, canvas_height):
        """Update ball position"""
        # Save previous position
        prev_x = self.x
        prev_y = self.y

        # Update position
        self.x += self.speed_x
        self.y += self.speed_y

        # To ensure constant speed when ball goes in other angles
        total_speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
        if abs(total_speed - self.base_speed) > 0.1:
            scale = self.base_speed / total_speed
            self.speed_x *= scale
            self.speed_y *= scale

        # To verify if ball is out of bounds of the canvas
        if self.y + self.radius > canvas_height:
            self.y = canvas_height - self.radius
            self.speed_y *= -1
        elif self.y - self.radius < 0:
            self.y = self.radius
            self.speed_y *= -1

    def reset(self, x, y, base_speed=None):
        """Reset ball position and velocity after scoring"""
        self.x = x
        self.y = y
        
        # Reset ball speed
        if base_speed is not None:
            self.base_speed = base_speed

        # Always ensure constant x velocity
        while abs(self.speed_y) < 2:  # Ensure y velocity is greater than 2
            angle = random.uniform(-0.5, 0.5)  # Random serve angle
            self.speed_x = self.base_speed * (
                1 if random.random() > 0.5 else -1
            )  # Constant x velocity
            self.speed_y = self.base_speed * math.sin(
                angle
            )  # Variable y velocity (based on angle)

    def serialize(self):
        """Serializes the ball state"""
        return {
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "speed_x": self.speed_x,
            "speed_y": self.speed_y,
        }