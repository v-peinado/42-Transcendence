class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.target_y = y  													# Para movimiento suave
        self.moving = 0  													# -1: arriba, 0: parado, 1: abajo
        
    def move(self, direction, canvas_height):
        direction = int(direction)
        
        move_amount = self.speed * direction								# Movimiento de la pala
        new_y = self.y + move_amount
        
        self.y = max(0, min(new_y, canvas_height - self.height))			# Limitar rango de movimiento de la pala al terreno

    def update(self, canvas_height):
        if self.target_y is not None:
            # Movimiento suave hacia el objetivo
            diff = self.target_y - (self.y + self.height/2)					# Diferencia entre la posición actual y el objetivo
            if abs(diff) > 5: 												# Esta línea evita oscilaciones indeseadas de la pala : Si la diferencia es mayor a 5 pixeles
                direction = 1 if diff > 0 else -1							# Mover hacia arriba o abajo
                self.move(direction, canvas_height)							# Mover la pala
            
    def serialize(self):													# Serialización de la pala (para enviar al cliente)
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'score': self.score
        }