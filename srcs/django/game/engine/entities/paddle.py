class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=15):  # Aumentamos más la velocidad base
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
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
        if self.moving != 0:
            self.move(self.moving, canvas_height)
            
    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'score': self.score
        }