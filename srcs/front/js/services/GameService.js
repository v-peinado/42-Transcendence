import AuthService from './AuthService.js';

class GameService {
	/**
	 * Verify if a game exists and the user has access to it
	 * @param {string|number} gameId - ID of the game to verify
	 * @returns {Promise<{exists: boolean, canAccess: boolean}>}
	 */
	static async verifyGameAccess(gameId) {
		try {
			// Auth check before making the request
			const token = localStorage.getItem('accessToken');
			if (!token) {
				return { exists: false, can_access: false };
			}

			// Data recovery if the user has already accessed the game
			const savedData = localStorage.getItem(`game_${gameId}`);
			if (savedData) {
				// if the user has already accessed the game, we assume they can access it
				return { exists: true, can_access: true };
			}

			// Backend request to confirm the game exists and the user can access it
			const response = await fetch(`/api/game/verify/${gameId}/`, {
				method: 'GET',
				headers: {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				}
			});
			// If the request fails, we assume the game does not exist
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
			// In case of error, we assume the game does not exist
			return { exists: false, can_access: false };
		}
	}
}

export default GameService;
