class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):  # Ajustado a 7 como en el original
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.target_y = y  # Añadir target_y para movimiento suave
        self.moving = 0  # -1: arriba, 0: parado, 1: abajo
        
    def move(self, direction, canvas_height):
        direction = int(direction)
        print(f"Moving paddle from y={self.y} with direction={direction}")
        
        # Cálculo directo de la nueva posición
        move_amount = self.speed * direction
        new_y = self.y + move_amount
        
        # Asegurar que la pala permanece dentro del canvas
        self.y = max(0, min(new_y, canvas_height - self.height))
        print(f"Paddle moved to y={self.y}, move_amount={move_amount}")

    def update(self, canvas_height):
        """Actualización suave hacia el objetivo"""
        if self.target_y is not None:
            # Movimiento suave hacia el objetivo
            diff = self.target_y - (self.y + self.height/2)
            if abs(diff) > 5:  # Zona muerta de 5 píxeles
                direction = 1 if diff > 0 else -1
                self.move(direction, canvas_height)
            
    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'score': self.score
        }