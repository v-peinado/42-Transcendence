import AuthService from './AuthService.js';

class GameService {
	static API_URL = '/api/game';

	/**
	 * Verifica si una partida existe y el usuario tiene acceso a ella
	 * @param {string|number} gameId - ID de la partida
	 * @returns {Promise<{exists: boolean, canAccess: boolean}>}
	 */
	static async verifyGameAccess(gameId) {
		try {
			// Verificar autenticación
			const token = localStorage.getItem('accessToken');
			if (!token) {
				return { exists: false, canAccess: false };
			}

			// Verificar si la partida existe
			const response = await fetch(`${this.API_URL}/verify/${gameId}/`, {
				method: 'GET',
				headers: {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				return { exists: false, canAccess: false };
			}

			const data = await response.json();
			return {
				exists: data.exists || false,
				canAccess: data.can_access || false
			};
		} catch (error) {
			console.error('Error verificando partida:', error);
			return { exists: false, canAccess: false };
		}
	}
}

export default GameService;
