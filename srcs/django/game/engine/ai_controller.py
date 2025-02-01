import random
import time

class AIController:
    DIFFICULTY_SETTINGS = {
        'easy': {
            'RANDOMNESS': 60,
            'MISS_CHANCE': 0.3,
            'AI_REACTION_DELAY': 300,
            'BALL_SPEED': 7
        },
        'medium': {
            'RANDOMNESS': 40,
            'MISS_CHANCE': 0.1,
            'AI_REACTION_DELAY': 200,
            'BALL_SPEED': 7
        },
        'hard': {
            'RANDOMNESS': 20,
            'MISS_CHANCE': 0.05,
            'AI_REACTION_DELAY': 100,
            'BALL_SPEED': 9
        },
        'nightmare': {
            'RANDOMNESS': 10,
            'MISS_CHANCE': 0.01,
            'AI_REACTION_DELAY': 50,
            'BALL_SPEED': 12
        }
    }

    def __init__(self, game_state):
        self.game_state = game_state
        self.last_update = 0
        self.last_prediction_time = 0
        self.prediction_interval = 1/30
        self.update_interval = 1.0

    def update(self, current_time):
        """Actualiza la posición de la pala AI"""
        if current_time - self.last_prediction_time >= self.prediction_interval:
            self.last_prediction_time = current_time
            self._update_paddle_position()

    def _update_paddle_position(self):
        """Actualiza la posición objetivo de la pala"""
        paddle = self.game_state.paddles['right']
        settings = self.DIFFICULTY_SETTINGS[self.game_state.difficulty]
        
        # Calcular posición objetivo
        predicted_y = self._predict_ball_y()
        
        # Añadir aleatoriedad
        randomness = (random.random() * settings['RANDOMNESS']) - (settings['RANDOMNESS'] / 2)
        
        # Simular errores humanos
        if random.random() < settings['MISS_CHANCE']:
            target_y = random.random() * self.game_state.canvas_height
        else:
            target_y = predicted_y + randomness
        
        # Ajustar target_y para el centro de la pala
        target_y -= paddle.height / 2
        
        # Limitar al canvas
        target_y = max(0, min(self.game_state.canvas_height - paddle.height, target_y))
        
        # Actualizar objetivo de la pala
        paddle.target_y = target_y
        paddle.update(self.game_state.canvas_height)

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
        
        return max(self.game_state.ball.radius, 
                  min(self.game_state.canvas_height - self.game_state.ball.radius, predicted_y))
