class Ball:
    def __init__(self, x, y, radius=10, speed_x=2, speed_y=2):
        """ Setear valores iniciales de la bola """
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = speed_x
        self.speed_y = speed_y
        
    def update(self, canvas_width, canvas_height):
        """ Actualizar la posición de la bola en cada frame """
        self.x += self.speed_x
        self.y += self.speed_y
        
        if self.y - self.radius <= 0 or self.y + self.radius >= canvas_height:		# Colisión con paredes superior e inferior
            self.speed_y *= -1
            
    def reset(self, x, y):
        """ Resetear la posición de la bola después de que un jugador anote """
        self.x = x
        self.y = y
        self.speed_x = 2 * (-1 if self.speed_x > 0 else 1)
        self.speed_y = 2 
        
    def serialize(self):
        """ Serializar la bola para enviarla a los clientes """
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y
        }