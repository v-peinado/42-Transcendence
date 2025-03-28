import { showGameOverModal, hideGameOverModal } from '../components/GameOverModal.js';

class GameModalService {
    constructor() {
        this.currentModal = null;
    }

    showGameOver({ final_score, winner, returnUrl, returnText, playerSide, isTournament = false, nextMatch = null, customButtons = [] }) {

        const scores = {
            player1: final_score?.player1 || 0,
            player2: final_score?.player2 || 0
        };

        const player1 = {
            username: final_score?.player1_name || 'Jugador 1',
            ...final_score?.player1_info
        };

        const player2 = {
            username: final_score?.player2_name || 'Jugador 2',
            ...final_score?.player2_info
        };

        // Asegurar que siempre pasamos un array de botones
        const options = {
            customButtons: Array.isArray(customButtons) ? customButtons : [],
            nextMatch
        };

        showGameOverModal(winner, player1, player2, scores, options);
    }

    hideGameOver() {
        hideGameOverModal();
    }
}

export default new GameModalService();
