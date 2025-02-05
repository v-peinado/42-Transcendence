from ..ai_controller import AIController  # Añadir esta importación

class GameModeManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def set_single_player(self, is_single, difficulty='medium'):
        """Configura el modo de juego"""
        self.game_state.is_single_player = is_single
        if is_single:
            self._configure_single_player(difficulty)
        else:
            self._configure_multiplayer()

    def _configure_single_player(self, difficulty):
        self.game_state.difficulty = difficulty
        self.game_state.ai_controller = AIController(self.game_state)  # Usar AIController directamente
        self.game_state.ai_controller.apply_difficulty_settings(difficulty)
        self._apply_difficulty_speed()

    def _configure_multiplayer(self):
        self.game_state.difficulty = None
        self.game_state.ai_controller = None
        self.game_state.ball.speed_x = self.game_state.MULTIPLAYER_SPEED
        self.game_state.ball.speed_y = 0

    def _apply_difficulty_speed(self):
        if self.game_state.is_single_player and self.game_state.ai_controller:
            settings = self.game_state.ai_controller.DIFFICULTY_SETTINGS[self.game_state.difficulty]
            direction = 1 if self.game_state.ball.speed_x >= 0 else -1
            self.game_state.ball.speed_x = settings['BALL_SPEED'] * direction
            self.game_state.ball.speed_y = settings['BALL_SPEED']
