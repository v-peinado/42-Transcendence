import random
from collections import deque

class AIController:
    """
    Controlador de la IA para el modo single player
    Gestiona el comportamiento y la toma de decisiones de la pala derecha (CPU)
    """
    DIFFICULTY_SETTINGS = {
        'easy': {
            'RANDOMNESS': 100,
            'MISS_CHANCE': 0.80,
            'AI_REACTION_DELAY': 200,  # Reducido de 400 a 200
            'BALL_SPEED': 3
        },
        'medium': {
            'RANDOMNESS': 40,
            'MISS_CHANCE': 0.1,
            'AI_REACTION_DELAY': 100,  # Reducido de 200 a 100
            'BALL_SPEED': 4
        },
        'hard': {
            'RANDOMNESS': 20,
            'MISS_CHANCE': 0.05,
            'AI_REACTION_DELAY': 50,   # Reducido de 100 a 50
            'BALL_SPEED': 7
        },
        'nightmare': {
            'RANDOMNESS': 10,
            'MISS_CHANCE': 0.01,
            'AI_REACTION_DELAY': 25,   # Reducido de 50 a 25
            'BALL_SPEED': 10
        }
    }

    def __init__(self, game_state):
        """Inicialización del controlador de la IA"""
        self.game_state = game_state
        self.last_update = 0
        self.last_prediction_time = 0
        self.prediction_interval = 1/60  # Aumentado de 1/30 a 1/60 para predicciones más frecuentes
        self.update_interval = 1.0
        self.current_target = None													# Añadir target actual (posición de la pala)
        self.last_decision_time = 0
        self.decision_interval = 0.1												# Tomar decisiones cada 100ms
        self.movement_cooldown = 1/120  # Aumentado de 1/60 a 1/120 para movimientos más suaves
        self.last_movement = 0
        self.position_history = deque(maxlen=5)										# Mantener últimas 5 posiciones (suavizado de movimientos)
        self.last_smooth_position = None
        self.smoothing_weight = 0.3													# Factor de suavizado (0-1)
        self.apply_difficulty_settings('medium')									# Inicializar con dificultad media 

    def update(self, current_time):
        """
        Actualiza la posición de la pala de la IA
        Args:
            current_time (float): Timestamp actual para controlar la frecuencia de actualización
        """
        if current_time - self.last_update >= self.reaction_delay / 1000:			# Convertir a segundos
            self.last_update = current_time
            if current_time - self.last_movement >= self.movement_cooldown:			# Añadir cooldown de movimiento (tiempo de espera entre movimientos)
                self.last_movement = current_time									# Actualizar tiempo del último movimiento
                # Actualizar predicción con menos frecuencia
                if current_time - self.last_prediction_time >= self.prediction_interval:
                    self._update_prediction()	
                    
                # Mover la pala usando el mismo sistema que el jugador
                paddle = self.game_state.paddles['right']							# Obtener pala derecha
                if self.current_target is not None:									# Si el target actual no es nulo (posición de la pala)
                    paddle.target_y = self.current_target							# Actualizar target de la pala
                    paddle.update(self.game_state.canvas_height)					# Actualizar posición de la pala

    def _update_prediction(self):
        """Actualiza la predicción de la IA"""
        paddle = self.game_state.paddles['right']
        settings = self.DIFFICULTY_SETTINGS[self.game_state.difficulty]				# Obtener configuración de dificultad
        
        # Actualizar predicción con menos frecuencia
        if self.game_state.ball.speed_x > 0:  # Si la pelota va hacia la IA
            predicted_y = self._predict_ball_y()
            
            # Reducir el efecto de la aleatoriedad para mejorar la precisión
            if random.random() < settings['MISS_CHANCE']:
                target_y = predicted_y + random.randint(-50, 50)  # Fallo más controlado
            else:
                randomness = (random.random() * settings['RANDOMNESS'] * 0.5) - (settings['RANDOMNESS'] * 0.25)
                target_y = int(predicted_y + randomness)
            
            # Añadir nueva posición al historial
            self.position_history.append(target_y)
            
            # Calcular posición suavizada
            if len(self.position_history) >= 2:
                # Media ponderada de las posiciones recientes
                smooth_target = self._calculate_smooth_position()
                
                # Transición suave desde la última posición
                if self.last_smooth_position is not None:
                    smooth_target = int(
                        self.last_smooth_position * (1 - self.smoothing_weight) +
                        smooth_target * self.smoothing_weight
                    )
                
                self.last_smooth_position = smooth_target
                target_y = smooth_target
        else:
             # Si la pelota va en dirección contraria, mover al centro suavemente
             target_y = self.game_state.canvas_height // 2

        # Ajustar posición final
        paddle_height = paddle.height
        target_y = max(0, min(target_y, self.game_state.canvas_height - paddle_height))
        self.current_target = target_y

    def _calculate_smooth_position(self):
        """
        Calcula una posición suavizada basada en el historial de posiciones
        Returns:
            int: Nueva posición Y suavizada para la pala
        """
        weights = [0.1, 0.15, 0.2, 0.25, 0.3]  											# Más tendencia a las posiciones recientes
        while len(weights) > len(self.position_history):
            weights.pop(0)
            
        weights = [w/sum(weights) for w in weights]  									# Normalizar pesos
        
        smooth_pos = 0
        for pos, weight in zip(self.position_history, weights):
            smooth_pos += pos * weight
            
        return int(smooth_pos)

    def _predict_ball_y(self):
        """Predice dónde intersectará la pelota"""
        if self.game_state.ball.speed_x <= 0:
            return self.game_state.ball.y
            
        sim_ball = {
            'x': self.game_state.ball.x,
            'y': self.game_state.ball.y,
            'speed_x': self.game_state.ball.speed_x,
            'speed_y': self.game_state.ball.speed_y,
            'radius': self.game_state.ball.radius
        }
        
        max_iterations = 500
        iterations = 0
        
        while sim_ball['x'] < self.game_state.paddles['right'].x and iterations < max_iterations:
            sim_ball['x'] += sim_ball['speed_x']
            sim_ball['y'] += sim_ball['speed_y']
            
            if sim_ball['y'] + sim_ball['radius'] >= self.game_state.canvas_height:
                sim_ball['y'] = self.game_state.canvas_height - sim_ball['radius']
                sim_ball['speed_y'] *= -1
            elif sim_ball['y'] - sim_ball['radius'] <= 0:
                sim_ball['y'] = sim_ball['radius']
                sim_ball['speed_y'] *= -1
                
            iterations += 1
            
        if iterations == max_iterations:
            return self.game_state.canvas_height / 2
            
        error_margin = 15
        random_error = (random.random() * 2 * error_margin) - error_margin
        predicted_y = sim_ball['y'] + random_error
        
        # Al final de la predicción, redondear el resultado
        predicted_y = int(sim_ball['y'])
        
        return max(self.game_state.ball.radius, 
                  min(self.game_state.canvas_height - self.game_state.ball.radius, predicted_y))

    def set_difficulty(self, difficulty):
        """Cambia la dificultad y actualiza todos los parámetros del juego"""
        self.game_state.difficulty = difficulty
        self.apply_difficulty_settings(difficulty)

    def apply_difficulty_settings(self, difficulty):
        """Aplica los parámetros de dificultad al estado del juego"""
        settings = self.DIFFICULTY_SETTINGS[difficulty]
        
        # Aplicar velocidad de la bola manteniendo la dirección
        direction_x = 1 if self.game_state.ball.speed_x > 0 else -1
        direction_y = 1 if self.game_state.ball.speed_y > 0 else -1
        
        # Actualizar velocidades de la bola
        self.game_state.ball.speed_x = direction_x * settings['BALL_SPEED']
        self.game_state.ball.speed_y = direction_y * settings['BALL_SPEED']
        
        # Actualizar parámetros de la IA
        self.reaction_delay = settings['AI_REACTION_DELAY']
