import random
import math

class Ball:		
    def __init__(self, x, y, radius=10):										# seteamos valores iniciales de la pelota
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = 0
        self.speed_y = 0
        self.base_speed = 7														# velocidad base de la pelota

    def update(self, canvas_width, canvas_height):
        """Para actualizar la posición de la pelota"""
        # Guardamos la posición anterior
        prev_x = self.x
        prev_y = self.y
        
        # Actualizamos la posición 
        self.x += self.speed_x
        self.y += self.speed_y

        # Para asegurar que la velocidad lineal se mantiene a pesar de que cambie el angulo
        total_speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
        if abs(total_speed - self.base_speed) > 0.1:
            scale = self.base_speed / total_speed
            self.speed_x *= scale
            self.speed_y *= scale
        
        # Para verificar las colisiones con los bordes del canvas (superior e inferior)
        if self.y + self.radius > canvas_height:
            self.y = canvas_height - self.radius
            self.speed_y *= -1
        elif self.y - self.radius < 0:
            self.y = self.radius
            self.speed_y *= -1
            
        # print(f"Ball update - pos:({self.x}, {self.y}), prev:({prev_x}, {prev_y}), speed:({self.speed_x}, {self.speed_y})")
            
    def reset(self, x, y):
        """Para resetear la posición y velocidad de la pelota después de un punto"""
        self.x = x
        self.y = y
        
        # Siempre aseguramos que la velocidad en x sea constante
        while abs(self.speed_y) < 2:												# Aseguramos que la velocidad en y sea mayor a 2
            angle = random.uniform(-0.5, 0.5)										# Angulo aleatorio de servicio
            self.speed_x = self.base_speed * (1 if random.random() > 0.5 else -1)	# Velocidad constante en x
            self.speed_y = self.base_speed * math.sin(angle)						# Velocidad variable en y (según el ángulo)
        
        # print(f"Ball reset - pos:({self.x}, {self.y}), speed:({self.speed_x}, {self.speed_y})")  # Debug

    def serialize(self):
        """Serializa el estado de la pelota"""
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y
        }