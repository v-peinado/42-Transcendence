class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=10):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        #self.moving = 0  # -1: arriba, 0: parado, 1: abajo
        
    def move(self, direction, canvas_height):
        if direction != 0:
            new_y = self.y + (self.speed * direction)
            # Mantener la paleta dentro del canvas
            self.y = max(0, min(new_y, canvas_height - self.height))
            print(f"Paddle moved to y={self.y}")  # Debug
            
    def serialize(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'score': self.score
        }