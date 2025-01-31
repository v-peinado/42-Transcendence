class Ball:
    def __init__(self, x, y, radius=10, speed_x=7, speed_y=7):  # Aumentada velocidad de 5 a 7
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.collision_cooldown = 0
        
    def update(self, canvas_width, canvas_height):
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1
            
        # Actualizar posición
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Colisiones con paredes superior e inferior
        if self.y - self.radius <= 0:
            self.y = self.radius  # Corregir posición
            self.speed_y = abs(self.speed_y)
        elif self.y + self.radius >= canvas_height:
            self.y = canvas_height - self.radius  # Corregir posición
            self.speed_y = -abs(self.speed_y)
            
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = abs(self.speed_x) * (-1 if self.speed_x > 0 else 1)
        self.speed_y = 5
        
    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y
        }

    def handle_paddle_collision(self, paddle_y, paddle_height):
        if self.collision_cooldown == 0:
            # Calcular punto de impacto relativo (0-1)
            relative_intersect_y = (paddle_y + (paddle_height / 2) - self.y) / (paddle_height / 2)
            # Convertir a ángulo (-45 a 45 grados)
            bounce_angle = relative_intersect_y * 0.785398  # 45 grados en radianes
            
            speed = (self.speed_x ** 2 + self.speed_y ** 2) ** 0.5
            self.speed_y = -speed * bounce_angle
            
            self.collision_cooldown = 5  # Prevenir colisiones múltiples