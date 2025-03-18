import AuthService from './AuthService.js';

class GameService {
    static async verifyGameAccess(gameId) {
        try {
            const token = localStorage.getItem('accessToken');
            if (!token) {
                return { exists: false, can_access: false };
            }

            const savedData = localStorage.getItem(`game_${gameId}`);
            if (savedData) {
                return { exists: true, can_access: true };
            }

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
            return { exists: false, can_access: false };
        }
    }
}

export default GameService;
