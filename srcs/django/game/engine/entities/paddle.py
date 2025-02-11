class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):
        """Setear valores iniciales de la pala"""
        self.x = int(x)															# Redondear posición inicial
        self.y = int(y)
        self.width = width
        self.height = height
        self.speed = speed														# Velocidad constante para todas las palas
        self.score = 0
        self.target_y = int(y)													# Redondear target inicial
        self.last_position = int(y)												# Añadir última posición para comparar

    def move(self, direction, canvas_height):
        """ Control de velocidad de movimiento de la pala """
        move_amount = self.speed * int(direction)								# Usar siempre la misma velocidad base
        new_y = self.y + move_amount
        self.y = int(max(0, min(new_y, canvas_height - self.height)))			# Redondear la posición y asegurar que no se sale de los límites

    def update(self, canvas_height):
        """ Actualiza la posición de la pala sin vibraciones """
        if self.target_y is not None:
            current_center = self.y + (self.height / 2)							# Calcular el centro actual de la pala
            target_center = self.target_y + (self.height / 2)					# Calcular el centro objetivo de la pala
            diff = round(target_center - current_center)						# Redondear la diferencia para evitar errores de redondeo
            
            # print(f"Paddle update - pos:{self.y}, target:{self.target_y}, diff:{diff}")  # Debug
            
            dead_zone = 7														# La zona muerta es de 7 píxeles para evitar vibraciones
            
            if abs(diff) > dead_zone:
                # Normalizar la velocidad de movimiento
                direction = 1 if diff > 0 else -1
                # Usar exactamente la misma velocidad que el jugador
                self.move(direction, canvas_height)
            elif self.y != self.last_position:
                # Si estamos en la zona muerta, forzar la posición exacta
                self.y = int(self.target_y)
            
            # Guardar la última posición
            self.last_position = self.y

    def serialize(self):
        """Serializar la pala para enviarla a los clientes"""
        return {
            'x': self.x,
            'y': int(self.y),                                               # Asegurar que la posición serializada es un entero (para evitar errores de redondeo)
            'width': self.width,
            'height': self.height,
            'score': self.score
        }