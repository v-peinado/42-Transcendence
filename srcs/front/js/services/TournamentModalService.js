import { showTournamentGameOverModal, hideTournamentGameOverModal, showTournamentMatchModal } from '../components/TournamentModals.js';

class TournamentModalService {
    showGameOver({ final_score, winner, nextMatch = null, customButtons = [] }) {
        const scores = {
            player1: final_score?.player1 || 0,
            player2: final_score?.player2 || 0
        };

        const player1 = {
            username: final_score?.player1_name || 'Jugador 1'
        };

        const player2 = {
            username: final_score?.player2_name || 'Jugador 2'
        };

        showTournamentGameOverModal(winner, player1, player2, scores, {
            nextMatch,
            customButtons: customButtons.map(btn => ({
                ...btn,
                className: `tournament-button ${btn.text === 'Siguiente Partido' ? 'primary' : 'secondary'}`,
                style: 'margin: 0.5rem;',
                containerClass: 'tournament-action-buttons' // Asegurarnos de que se use la clase correcta
            }))
        });
    }

    hideGameOver() {
        hideTournamentGameOverModal();
    }

    showMatchStart(player1, player2) {
        showTournamentMatchModal(player1, player2);
    }
}

export default new TournamentModalService();
