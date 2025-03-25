import { showTournamentGameOverModal, hideTournamentGameOverModal, showTournamentMatchModal } from '../components/TournamentModals.js';
import TournamentService from './TournamentService.js';

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

        // Si no hay siguiente partido, mostrar el resumen del torneo
        if (!nextMatch && final_score.tournament_id) {  // Verificar que existe tournament_id
            customButtons = [{
                text: '🏆 Ver Campeón del Torneo',
                onClick: () => this.showTournamentSummary(final_score.tournament_id),
                className: 'tournament-button primary'
            }];
        }

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

    async showTournamentSummary(tournamentId) {
        try {
            const modal = document.getElementById('tournamentSummaryModal');
            if (!modal) {
                console.error('Modal de resumen no encontrado en el DOM');
                return;
            }

            const tournamentData = await TournamentService.getTournamentDetails(tournamentId);
            console.log('Datos del torneo:', tournamentData);

            // Asegurar que el contenedor existe
            const rankingList = modal.querySelector('#tournamentRankingList');
            if (!rankingList) {
                console.error('Contenedor del ranking no encontrado');
                return;
            }

            // Mostrar el ganador con estilo mejorado
            rankingList.innerHTML = `
                <div class="ranking-item winner-item">
                    <div class="ranking-info text-center">
                        <i class="fas fa-crown" style="color: #ffd700; font-size: 2.5rem; margin-bottom: 1rem;"></i>
                        <div class="ranking-name champion-name">
                            ${tournamentData.winner}
                        </div>
                        <div class="champion-label">Campeón del Torneo</div>
                    </div>
                </div>
            `;

            modal.style.display = 'flex';
        } catch (error) {
            console.error('Error detallado al mostrar el resumen del torneo:', error);
        }
    }
}

export default new TournamentModalService();
