import time

class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):
        """Set initial paddle values"""
        self.x = int(x)
        self.y = int(y)
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.target_y = int(y)
        self.last_position = int(y)
        self.moving = False
        self.ready_for_input = True
        self.last_direction = 0
        self.last_update_time = 0

    def move(self, direction, canvas_height):
        """Control paddle movement speed"""
        if not self.ready_for_input:
            return

        # Save last direction for interpolation
        self.last_direction = direction
        
        # If direction is 0, stop moving
        if direction == 0:
            self.moving = False
            self.target_y = self.y
            return
            
        self.moving = True
        
        move_amount = self.speed * int(direction)  # Always use same base speed
        new_y = self.y + move_amount
        
        # Is in the limits of the canvas?
        self.y = int(
            max(0, min(new_y, canvas_height - self.height))
        )  # Round position and ensure bounds
        
        # Set target position for interpolation
        self.target_y = self.y
        self.last_position = self.y
        self.last_update_time = time.time() * 1000  # ms

    def update(self, canvas_height):
        """Update paddle position without vibrations"""
        if not self.moving or not self.ready_for_input:	# if not moving or not ready for input,
            return
            
        if self.target_y is not None:
            current_center = self.y + (self.height / 2)  # Calculate current paddle center
            target_center = self.target_y + (self.height / 2)  # Calculate target paddle center
            diff = round(target_center - current_center)  # Round difference to avoid rounding errors

            dead_zone = 7  # Dead zone is 7 pixels to avoid vibrations

            if abs(diff) > dead_zone:
                direction = 1 if diff > 0 else -1  # Calculate direction based on difference
                self.move(direction, canvas_height)  # Use the same move method to avoid code duplication
            elif self.y != self.last_position:  # If we are in the dead zone and the paddle has moved...
                self.y = int(self.target_y)  # Set the paddle to the target position

            self.last_position = self.y  # Save last position for comparison

    def reset_state(self, y=None):
        """Reset paddle state completely, optionally with new y position"""
        
        # Reset all values to default in case of a new game
        if y is not None:
            self.y = int(y)
        
        self.target_y = self.y
        self.last_position = self.y
        self.moving = False
        self.last_direction = 0
        
        # Important: Do not disable input during reset
        self.ready_for_input = True
        
        # IEnsure speed is maintained at original value
        if not hasattr(self, 'original_speed'):
            self.original_speed = self.speed
        else:
            self.speed = self.original_speed

    def serialize(self):
        """Serializes the paddle state"""
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
