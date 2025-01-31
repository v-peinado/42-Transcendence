class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=15):  # Aumentar velocidad base
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.target_y = y  # Añadir posición objetivo
        
    def move(self, direction, canvas_height):
        if direction != 0:
            self.target_y = self.y + (self.speed * direction)
            # Aplicar límites
            self.target_y = max(0, min(self.target_y, canvas_height - self.height))
            # Mover directamente
            self.y = self.target_y
            print(f"[PADDLE] Moved to y={self.y}")
            
    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'score': self.score
        }