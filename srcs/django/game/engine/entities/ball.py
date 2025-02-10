class Ball:
    def __init__(self, x, y, speed_x=0, speed_y=0, radius=10):
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.radius = radius

    def update(self, canvas_width, canvas_height):
        """ Actualizar la posición de la bola en cada frame """
        self.x += self.speed_x
        self.y += self.speed_y
        
        if self.y - self.radius <= 0 or self.y + self.radius >= canvas_height:		# Colisión con paredes superior e inferior
            self.speed_y *= -1
            
    def reset(self, x, y):
        """Resetea la posición de la pelota"""
        self.x = x
        self.y = y
        self.speed_x = 0
        self.speed_y = 0

    def serialize(self):
        """Serializa el estado de la pelota"""
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y
        }