import AuthService from './AuthService.js';

class GameService {
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
				return { exists: false, can_access: false };
			}

			// Recuperar datos guardados si existen
			const savedData = localStorage.getItem(`game_${gameId}`);
			if (savedData) {
				// Si tenemos datos guardados, el usuario probablemente tiene acceso
				return { exists: true, can_access: true };
			}

			// Solicitud genérica al backend para confirmar existencia de la partida
			const response = await fetch(`/api/game/verify/${gameId}/`, {
				method: 'GET',
				headers: {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				console.warn(`Error verificando partida ${gameId}: ${response.status}`);
				return { exists: false, can_access: false };
			}

			const data = await response.json();
			return {
				exists: data.exists || false,
				can_access: data.can_access || false
			};
		} catch (error) {
			console.error('Error verificando partida:', error);
			// En caso de error de red, asumimos que la partida existe si tenemos el ID
			return { exists: true, can_access: true };
		}
	}
}

export default GameService;
