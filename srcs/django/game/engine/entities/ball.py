import random
import math


class Ball:
    def __init__(self, x, y, radius=10):  # Set initial ball values
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = 7

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

        # print(f"Ball update - pos:({self.x}, {self.y}), prev:({prev_x}, {prev_y}), speed:({self.speed_x}, {self.speed_y})")

    def reset(self, x, y):
        """Reset ball position and velocity after scoring"""
        self.x = x
        self.y = y
        
        # Asegurar que la velocidad sea la original
        self.base_speed = 7  # Confirmar que usamos la velocidad base original
        
        # Generar un ángulo aleatorio entre -45 y 45 grados (o 135 y 225 grados)
        angle = random.uniform(-45, 45)
        # 50% de probabilidad de ir hacia la izquierda o derecha
        if random.random() < 0.5:
            angle += 180  # Hacia la izquierda
        
        # Convertir el ángulo a radianes
        angle_rad = math.radians(angle)
        
        # Calcular las componentes de velocidad basadas en el ángulo y la velocidad base
        self.speed_x = self.base_speed * math.cos(angle_rad)
        self.speed_y = self.base_speed * math.sin(angle_rad)

    def serialize(self):
        """Serializa el estado de la pelota"""
        return {
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "speed_x": self.speed_x,
            "speed_y": self.speed_y,
        }
