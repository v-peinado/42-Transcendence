/**
 * Utilidad para interpolar estados de juego, especialmente útil en reconexiones
 */
class GameStateInterpolator {
	/**
	 * Interpola entre dos estados del juego
	 * @param {Object} stateA - Estado inicial
	 * @param {Object} stateB - Estado final
	 * @param {number} factor - Factor de interpolación (0-1)
	 * @returns {Object} Estado interpolado
	 */
	static interpolate(stateA, stateB, factor) {
		if (!stateA || !stateB || factor < 0 || factor > 1) {
			return stateB || stateA || {};
		}

		// Crear un nuevo estado base
		const interpolated = {
			status: stateB.status, // Usar siempre el estado más reciente
			paddles: {},
			server_timestamp: stateB.server_timestamp,
			reconnection_sync: stateB.reconnection_sync
		};

		// Interpolar la pelota si existe en ambos estados
		if (stateA.ball && stateB.ball) {
			// OPTIMIZACIÓN: Mejorar la interpolación para movimientos no lineales
			// Añadir un pequeño factor de predicción basado en velocidad
			const predictiveFactor = 0.2; // 20% de predicción
			const predictedX = stateB.ball.x + (stateB.ball.speed_x * predictiveFactor);
			const predictedY = stateB.ball.y + (stateB.ball.speed_y * predictiveFactor);

			interpolated.ball = {
				// Interpolar con algo de predicción para movimientos más suaves
				x: stateA.ball.x + (predictedX - stateA.ball.x) * factor,
				y: stateA.ball.y + (predictedY - stateA.ball.y) * factor,
				radius: stateB.ball.radius,
				speed_x: stateB.ball.speed_x,
				speed_y: stateB.ball.speed_y,
				prev_x: stateA.ball.x,
				prev_y: stateA.ball.y,
				last_update: stateB.ball.last_update
			};
		} else {
			interpolated.ball = stateB.ball || stateA.ball;
		}

		// Interpolar las palas
		if (stateA.paddles && stateB.paddles) {
			// Interpolar cada pala
			for (const side of ['left', 'right']) {
				const paddleA = stateA.paddles[side];
				const paddleB = stateB.paddles[side];

				if (paddleA && paddleB) {
					// OPTIMIZACIÓN: Si la pala está en movimiento, usar interpolación con easing
					const isMoving = paddleB.moving;
					let interpolationFactor = factor;

					// Aplicar una curva de easing para movimientos más naturales
					if (isMoving) {
						// Usar una función de easing para acelerar/desacelerar el movimiento
						interpolationFactor = this._easeInOutQuad(factor);
					}

					interpolated.paddles[side] = {
						...paddleB, // Copiar propiedades del estado B como base
						y: paddleA.y + (paddleB.y - paddleA.y) * interpolationFactor,
						last_position: paddleA.y
					};
				} else {
					interpolated.paddles[side] = paddleB || paddleA;
				}
			}
		} else {
			interpolated.paddles = stateB.paddles || stateA.paddles;
		}

		// Mantener puntuaciones del estado más reciente
		if (interpolated.paddles && stateB.paddles) {
			if (interpolated.paddles.left) {
				interpolated.paddles.left.score = stateB.paddles.left?.score || 0;
			}
			if (interpolated.paddles.right) {
				interpolated.paddles.right.score = stateB.paddles.right?.score || 0;
			}
		}

		return interpolated;
	}

	/**
	 * Función de easing para movimientos más suaves
	 * @param {number} t - Valor entre 0 y 1
	 * @returns {number} Valor de easing entre 0 y 1
	 */
	static _easeInOutQuad(t) {
		return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
	}

	/**
	 * Simula el movimiento de la pelota basado en su velocidad y el tiempo transcurrido
	 * para proporcionar una transición más suave durante las reconexiones.
	 * 
	 * @param {Object} state - Estado actual
	 * @param {number} elapsedTimeMs - Tiempo transcurrido en milisegundos
	 * @returns {Object} Estado con la pelota en su posición predicha
	 */
	static predictBallPosition(state, elapsedTimeMs) {
		if (!state || !state.ball || !state.ball.speed_x || !state.ball.speed_y) {
			return state;
		}

		// Clonar estado para no modificar el original
		const newState = JSON.parse(JSON.stringify(state));

		// Calcular posición predicha
		const timeFactorSeconds = elapsedTimeMs / 1000;
		newState.ball.prev_x = newState.ball.x;
		newState.ball.prev_y = newState.ball.y;
		newState.ball.x += newState.ball.speed_x * timeFactorSeconds;
		newState.ball.y += newState.ball.speed_y * timeFactorSeconds;

		// Gestionar rebotes simples para evitar que la pelota se salga del campo
		// (sin colisiones con palas, solo con los bordes superior e inferior)
		const radius = newState.ball.radius || 5;

		// Rebote superior e inferior
		if (newState.ball.y - radius < 0 && newState.ball.speed_y < 0) {
			newState.ball.y = radius;
			newState.ball.speed_y = -newState.ball.speed_y;
		} else if (newState.ball.y + radius > 600 && newState.ball.speed_y > 0) {
			newState.ball.y = 600 - radius;
			newState.ball.speed_y = -newState.ball.speed_y;
		}

		return newState;
	}

	/**
	 * Crea una secuencia de estados intermedios para una transición suave
	 * @param {Object} stateA - Estado inicial
	 * @param {Object} stateB - Estado final
	 * @param {number} steps - Número de pasos intermedios
	 * @returns {Array} Secuencia de estados interpolados
	 */
	static createTransitionSequence(stateA, stateB, steps) {
		const sequence = [];

		// OPTIMIZACIÓN: Usar una curva de easing para distribución no lineal
		// de los estados intermedios para transiciones más naturales
		for (let i = 0; i <= steps; i++) {
			const linearFactor = i / steps;
			const easingFactor = this._easeInOutQuad(linearFactor);
			sequence.push(this.interpolate(stateA, stateB, easingFactor));
		}

		return sequence;
	}
}

export default GameStateInterpolator;
