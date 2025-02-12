class Paddle:
    def __init__(self, x, y, width=10, height=100, speed=7):
        """Set initial paddle values"""
        self.x = int(x)												# Round initial position
        self.y = int(y)
        self.width = width
        self.height = height
        self.speed = speed
        self.score = 0
        self.target_y = int(y)										# Round initial target
        self.last_position = int(y)									# Add last position for comparison

    def move(self, direction, canvas_height):
        """Control paddle movement speed"""
        move_amount = self.speed * int(direction)					# Always use same base speed
        new_y = self.y + move_amount
        self.y = int(
            max(0, min(new_y, canvas_height - self.height))
        )															# Round position and ensure bounds

    def update(self, canvas_height):
        """Update paddle position without vibrations"""
        if self.target_y is not None:
            current_center = self.y + (
                self.height / 2
            )														# Calculate current paddle center
            target_center = self.target_y + (
                self.height / 2
            )														# Calculate target paddle center
            diff = round(
                target_center - current_center
            )														# Round difference to avoid rounding errors

            dead_zone = 7											# Dead zone is 7 pixels to avoid vibrations

            if abs(diff) > dead_zone:
                direction = 1 if diff > 0 else -1					# Calculate direction based on difference	
                self.move(direction, canvas_height)					# Use the same move method to avoid code duplication
            elif self.y != self.last_position:						# If we are in the dead zone and the paddle has moved...
                self.y = int(self.target_y)							# Set the paddle to the target position

            self.last_position = self.y								# Save last position for comparison

    def serialize(self):
        """Serializar la pala para enviarla a los clientes"""
        return {
            "x": self.x,
            "y": int(
                self.y
            ),
            "width": self.width,
            "height": self.height,
            "score": self.score,
        }
