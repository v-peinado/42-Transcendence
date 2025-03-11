/**
 * Utilidad mínima para interpolar estados de juego
 */
class GameStateInterpolator {
	/**
	 * Interpola entre dos estados del juego
	 */
	static interpolate(stateA, stateB, factor) {
		if (!stateA || !stateB || factor < 0 || factor > 1) {
			return stateB || stateA || {};
		}

		// Crear un nuevo estado base
		const interpolated = {
			status: stateB.status,
			paddles: {},
		};

		// Interpolar la pelota
		if (stateA.ball && stateB.ball) {
			interpolated.ball = {
				x: stateA.ball.x + (stateB.ball.x - stateA.ball.x) * factor,
				y: stateA.ball.y + (stateB.ball.y - stateA.ball.y) * factor,
				radius: stateB.ball.radius,
				speed_x: stateB.ball.speed_x,
				speed_y: stateB.ball.speed_y
			};
		} else {
			interpolated.ball = stateB.ball || stateA.ball;
		}

		// Interpolar las palas
		if (stateA.paddles && stateB.paddles) {
			for (const side of ['left', 'right']) {
				const paddleA = stateA.paddles[side];
				const paddleB = stateB.paddles[side];

				if (paddleA && paddleB) {
					interpolated.paddles[side] = {
						...paddleB,
						y: paddleA.y + (paddleB.y - paddleA.y) * factor
					};
				} else {
					interpolated.paddles[side] = paddleB || paddleA;
				}
			}
		} else {
			interpolated.paddles = stateB.paddles || stateA.paddles;
		}

		// Mantener puntuaciones
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
	 * Crea una secuencia de estados intermedios para una transición suave
	 */
	static createTransitionSequence(stateA, stateB, steps) {
		const sequence = [];
		for (let i = 0; i <= steps; i++) {
			const factor = i / steps;
			sequence.push(this.interpolate(stateA, stateB, factor));
		}
		return sequence;
	}

	/**
	 * Predice la posición de la pelota basado en su velocidad
	 */
	static predictBallPosition(state, elapsedTimeMs) {
		if (!state || !state.ball || !state.ball.speed_x || !state.ball.speed_y) {
			return state;
		}

		const newState = JSON.parse(JSON.stringify(state));
		const timeFactorSeconds = elapsedTimeMs / 1000;

		newState.ball.x += newState.ball.speed_x * timeFactorSeconds;
		newState.ball.y += newState.ball.speed_y * timeFactorSeconds;

		// Rebotes simples arriba/abajo
		const radius = newState.ball.radius || 5;
		if (newState.ball.y - radius < 0 && newState.ball.speed_y < 0) {
			newState.ball.y = radius;
			newState.ball.speed_y = -newState.ball.speed_y;
		} else if (newState.ball.y + radius > 600 && newState.ball.speed_y > 0) {
			newState.ball.y = 600 - radius;
			newState.ball.speed_y = -newState.ball.speed_y;
		}

		return newState;
	}
}

export default GameStateInterpolator;
