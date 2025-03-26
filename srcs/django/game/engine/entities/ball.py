import random
import math
import time


class Ball:
    def __init__(self, x, y, radius=10, base_speed=9):  
        """Set initial ball values"""
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = base_speed
        self.last_update_time = 0
        self.prev_x = x
        self.prev_y = y

    def update(self, canvas_width, canvas_height):
        """Update ball position"""
        # Save previous position
        self.prev_x = self.x
        self.prev_y = self.y

        # Update position
        self.x += self.speed_x
        self.y += self.speed_y

        # To ensure constant speed when ball goes in other angles
        # Total speed represents the magnitude of the ball's velocity
        total_speed = math.sqrt(self.speed_x**2 + self.speed_y**2) # Total speed = square root of x^2 + y^2 
        if abs(total_speed - self.base_speed) > 0.1: # If total speed is not equal to base speed
            scale = self.base_speed / total_speed	# Scale = base speed / total speed
            self.speed_x *= scale	# Multiply x speed by scale
            self.speed_y *= scale	# Multiply y speed by scale

        # To verify if ball is out of bounds of the canvas
        if self.y + self.radius > canvas_height:
            self.y = canvas_height - self.radius
            self.speed_y *= -1
        elif self.y - self.radius < 0:
            self.y = self.radius
            self.speed_y *= -1
            
        # Save last update time
        self.last_update_time = time.time() * 1000  # ms

    def reset(self, x, y, base_speed=None):
        """Reset ball position and velocity after scoring"""
        self.prev_x = self.x
        self.prev_y = self.y
        
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
            "prev_x": self.prev_x,
            "prev_y": self.prev_y,
            "radius": self.radius,
            "speed_x": self.speed_x,
            "speed_y": self.speed_y,
            "last_update": self.last_update_time
        }
