export function showTournamentGameOverModal(winner, player1, player2, scores, options = {}) {
    const modal = document.getElementById('tournamentGameOverScreen');
    if (!modal) {
        console.error('Modal not found in DOM');
        return;
    }

    // Actualizar elementos del modal
    const winnerText = modal.querySelector('#winnerText');
    const player1Name = modal.querySelector('#finalPlayer1Name');
    const player2Name = modal.querySelector('#finalPlayer2Name');
    const player1Score = modal.querySelector('.player1-score');
    const player2Score = modal.querySelector('.player2-score');
    const buttonsContainer = modal.querySelector('.tournament-action-buttons');

    // Verificar que todos los elementos existen
    if (!winnerText || !player1Name || !player2Name || !player1Score || !player2Score || !buttonsContainer) {
        console.error('One or more elements not found in modal');
        return;
    }

    // Establecer contenido
    winnerText.textContent = `¡${winner} ha ganado!`;
    player1Name.textContent = player1.username;
    player2Name.textContent = player2.username;
    player1Score.textContent = scores.player1;
    player2Score.textContent = scores.player2;

    // Limpiar y añadir botones
    buttonsContainer.innerHTML = '';
    if (options.customButtons) {
        options.customButtons.forEach(btn => {
            const button = document.createElement('button');
            button.className = btn.className || '';
            button.textContent = btn.text;
            if (btn.style) button.style = btn.style;
            button.onclick = btn.onClick;
            buttonsContainer.appendChild(button);
        });
    }

    // Mostrar el modal
    modal.style.display = 'flex';
}

export function hideTournamentGameOverModal() {
    const gameOverScreen = document.getElementById('tournamentGameOverScreen'); // Cambiar ID
    if (gameOverScreen) {
        gameOverScreen.style.display = 'none';
    }
}

export function showTournamentMatchModal(player1, player2) {

    const matchFoundModal = document.getElementById('tournamentMatchFoundModal');
    if (!matchFoundModal) {
        console.error('Modal de inicio de partido no encontrado');
        return;
    }

    try {
        // Asegurarnos de que el modal de game over esté oculto
        const gameOverScreen = document.getElementById('tournamentGameOverScreen');
        if (gameOverScreen) {
            gameOverScreen.style.display = 'none';
        }

        // Asegurarnos que los elementos existen y actualizar nombres
        const player1Element = matchFoundModal.querySelector('#player1NamePreMatch');
        const player2Element = matchFoundModal.querySelector('#player2NamePreMatch');

        if (player1Element && player2Element) {
            player1Element.textContent = player1.username || 'Jugador 1';
            player2Element.textContent = player2.username || 'Jugador 2';
        } else {
            console.error('No se encontraron los elementos para los nombres de jugadores');
        }

        // Mostrar modal y asegurar visibilidad
        matchFoundModal.style.display = 'flex';
        matchFoundModal.style.visibility = 'visible';
        matchFoundModal.style.opacity = '1';
    } catch (error) {
        console.error('Error al mostrar modal de inicio:', error);
    }
}
