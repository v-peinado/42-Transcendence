import random
import math

class Ball:
    def __init__(self, x, y, radius=10):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = 7  # Velocidad base constante

    def update(self, canvas_width, canvas_height):
        """Actualización con físicas corregidas"""
        # Guardar posición anterior para cálculos de colisión
        prev_x = self.x
        prev_y = self.y
        
        # Actualizar posición
        self.x += self.speed_x
        self.y += self.speed_y

        # Mantener velocidad constante
        total_speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
        if abs(total_speed - self.base_speed) > 0.1:
            scale = self.base_speed / total_speed
            self.speed_x *= scale
            self.speed_y *= scale
        
        # Solo verificar colisiones verticales aquí
        if self.y + self.radius > canvas_height:
            self.y = canvas_height - self.radius
            self.speed_y *= -1
        elif self.y - self.radius < 0:
            self.y = self.radius
            self.speed_y *= -1
            
        # Las colisiones horizontales (puntuación) se manejan en ScoreManager
        print(f"Ball update - pos:({self.x}, {self.y}), prev:({prev_x}, {prev_y}), speed:({self.speed_x}, {self.speed_y})")
            
    def reset(self, x, y):
        """Resetea la posición y velocidad de la pelota"""
        self.x = x
        self.y = y
        
        # Asegurar que siempre hay una velocidad inicial significativa
        while abs(self.speed_y) < 2:  # Mínimo componente vertical
            angle = random.uniform(-0.5, 0.5)
            self.speed_x = self.base_speed * (1 if random.random() > 0.5 else -1)
            self.speed_y = self.base_speed * math.sin(angle)
        
        print(f"Ball reset - pos:({self.x}, {self.y}), speed:({self.speed_x}, {self.speed_y})")  # Debug

    def serialize(self):
        """Serializa el estado de la pelota"""
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y
        }