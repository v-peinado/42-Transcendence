class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):
        """Setear valores iniciales de la pala"""
        self.x = int(x)  # Redondear posición inicial
        self.y = int(y)
        self.width = width
        self.height = height
        self.speed = speed  # Velocidad constante para todas las palas
        self.score = 0
        self.target_y = int(y)  # Redondear target inicial
        self.moving = 0
        self.last_position = int(y)  # Añadir última posición para comparar
        self.max_speed = speed  # Velocidad máxima constante para ambas palas
        
    def move(self, direction, canvas_height):
        """ Movimiento directo con velocidad fija """
        direction = int(direction)
        move_amount = self.speed * direction  # Usar siempre la misma velocidad base
        new_y = self.y + move_amount
        
        # Redondear la nueva posición
        self.y = int(max(0, min(new_y, canvas_height - self.height)))

    def update(self, canvas_height):
        """ Actualiza la posición de la pala con movimiento suavizado
        Args: canvas_height (int): Altura del canvas para limitar el movimiento """
        if self.target_y is not None:
            # Calcular el centro actual de la pala
            current_center = self.y + (self.height / 2)
            target_center = self.target_y + (self.height / 2)
            
            # Calcular la diferencia y redondearla
            diff = round(target_center - current_center)
            
            # Zona muerta más amplia para evitar micro-movimientos
            dead_zone = 7  # Aumentado de 5 a 7
            
            if abs(diff) > dead_zone:
                # Normalizar la velocidad de movimiento
                direction = 1 if diff > 0 else -1
                # Usar exactamente la misma velocidad que el jugador
                self.move(direction, canvas_height)
            else:
                # Si estamos en la zona muerta, forzar la posición exacta
                if self.y != self.last_position:
                    self.y = int(self.target_y)
            
            # Guardar la última posición
            self.last_position = self.y

    def serialize(self):
        """Serializar la pala para enviarla a los clientes"""
        return {
            'x': self.x,
            'y': int(self.y),  # Asegurar que la posición serializada es un entero
            'width': self.width,
            'height': self.height,
            'score': self.score
        }