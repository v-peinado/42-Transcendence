class Ball:
    def __init__(self, x, y, radius=10, speed_x=2, speed_y=2):  # Reducido de 3 a 2
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = speed_x
        self.speed_y = speed_y
        
    def update(self, canvas_width, canvas_height):
        # Actualizar posición
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Colisiones con paredes superior e inferior
        if self.y - self.radius <= 0 or self.y + self.radius >= canvas_height:
            self.speed_y *= -1
            
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = 2 * (-1 if self.speed_x > 0 else 1)  # Reducido a 2
        self.speed_y = 2  # Reducido a 2
        
    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y
        }