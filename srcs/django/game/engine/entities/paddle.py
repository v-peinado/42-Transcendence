import asyncio

class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):
        """Set initial paddle values"""
        self.x = int(x)  # Round initial position
        self.y = int(y)
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.target_y = int(y)  # Round initial target
        self.last_position = int(y)  # Add last position for comparison
        self.moving = False     # Flag to track if paddle is actively moving
        self.ready_for_input = True  # Nueva bandera para controlar si la pala está lista para recibir comandos
        self.last_direction = 0  # Nuevo: Mantener el último comando de dirección
        self.last_update_time = 0  # Timestamp del último update (para sincronización)

    def move(self, direction, canvas_height):
        """Control paddle movement speed"""
        if not self.ready_for_input:
            print(f"[PADDLE] Ignorando movimiento, pala no lista para input. Estado: {self.__dict__}")
            return

        # Guardar la última dirección recibida
        self.last_direction = direction
        
        # Si la dirección es 0, marcar como no en movimiento
        if direction == 0:
            print(f"[PADDLE] Deteniendo movimiento. Posición: {self.y}")
            self.moving = False
            # Al detenerse, asegurarse de que la posición objetivo coincide con la actual
            self.target_y = self.y
            return
            
        # Marcar como en movimiento si la dirección no es 0
        self.moving = True
        old_y = self.y
        
        move_amount = self.speed * int(direction)  # Always use same base speed
        new_y = self.y + move_amount
        
        # Asegurar que se mantiene dentro de los límites
        self.y = int(
            max(0, min(new_y, canvas_height - self.height))
        )  # Round position and ensure bounds
        
        # Actualizar la posición objetivo y última posición para seguimiento
        self.target_y = self.y
        self.last_position = self.y
        self.last_update_time = time.time() * 1000  # ms
        
        print(f"[PADDLE] Movimiento {direction}. Y: {old_y} -> {self.y}")

    def update(self, canvas_height):
        """Update paddle position without vibrations"""
        # Si no está en movimiento activo, no necesitamos actualizar
        if not self.moving or not self.ready_for_input:
            return
            
        if self.target_y is not None:
            current_center = self.y + (
                self.height / 2
            )  # Calculate current paddle center
            target_center = self.target_y + (
                self.height / 2
            )  # Calculate target paddle center
            diff = round(
                target_center - current_center
            )  # Round difference to avoid rounding errors

            dead_zone = 7  # Dead zone is 7 pixels to avoid vibrations

            if abs(diff) > dead_zone:
                direction = (
                    1 if diff > 0 else -1
                )  # Calculate direction based on difference
                self.move(
                    direction, canvas_height
                )  # Use the same move method to avoid code duplication
            elif (
                self.y != self.last_position
            ):  # If we are in the dead zone and the paddle has moved...
                self.y = int(self.target_y)  # Set the paddle to the target position

            self.last_position = self.y  # Save last position for comparison

    def reset_state(self, y=None):
        """Reset paddle state completely, optionally with new y position"""
        print(f"[PADDLE] Reset completo de la pala. Y anterior: {self.y}, Y nuevo: {y if y is not None else self.y}")
        
        # Temporalmente marcar como no listo para entrada mientras resetea
        self.ready_for_input = False
        
        # Reset completo de todas las variables relacionadas con el movimiento
        if y is not None:
            self.y = int(y)
        
        self.target_y = self.y
        self.last_position = self.y
        self.moving = False
        self.last_direction = 0
        
        # Volver a habilitar entrada después de un pequeño delay
        import asyncio
        def enable_input():
            self.ready_for_input = True
            print(f"[DEBUG] Paddle.reset_state - Pala lista para entrada de nuevo. Estado final: {self.__dict__}")
        
        # En entorno síncrono, habilitar inmediatamente
        self.ready_for_input = True
        
        print(f"[PADDLE] Estado final después del reset: y={self.y}, target={self.target_y}, moving={self.moving}")

    def serialize(self):
        """Serializar la pala para enviarla a los clientes"""
        return {
            "x": self.x,
            "y": int(self.y),
            "width": self.width,
            "height": self.height,
            "score": self.score,
            "moving": self.moving,
            "last_position": self.last_position,
            "target_y": self.target_y,
            "ready_for_input": self.ready_for_input,
            "last_direction": self.last_direction,
            "last_update": self.last_update_time
        }
