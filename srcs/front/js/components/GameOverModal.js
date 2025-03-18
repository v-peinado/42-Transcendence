export function showGameOverModal(winner, player1, player2, scores, isTournament = false) {
    const gameOverScreen = document.getElementById('gameOverScreen');
    if (!gameOverScreen) {
        console.error('Modal de game over no encontrado');
        return;
    }

    // Elementos requeridos para el modo single player
    const requiredElements = {
        winnerText: document.getElementById('winnerText'),
        finalPlayer1Name: document.getElementById('finalPlayer1Name'),
        finalPlayer2Name: document.getElementById('finalPlayer2Name'),
        player1Score: document.querySelector('.player1-score'),
        player2Score: document.querySelector('.player2-score'),
        returnButton: document.getElementById('returnToLobby'),
        playAgainButton: document.getElementById('playAgain')
    };

    // Verificar solo los elementos requeridos
    for (const [key, element] of Object.entries(requiredElements)) {
        if (!element) {
            console.error(`Elemento ${key} no encontrado en el modal`);
            return;
        }
    }

    try {
        // Actualizar textos
        requiredElements.winnerText.textContent = `¡${winner} ha ganado!`;
        requiredElements.finalPlayer1Name.textContent = player1.username;
        requiredElements.finalPlayer2Name.textContent = player2.username;
        
        // Asegurarnos que los scores son números
        const score1 = typeof scores.player1 === 'number' ? scores.player1 : parseInt(scores.player1) || 0;
        const score2 = typeof scores.player2 === 'number' ? scores.player2 : parseInt(scores.player2) || 0;
        
        requiredElements.player1Score.textContent = score1;
        requiredElements.player2Score.textContent = score2;

        console.log('Actualizando scores:', score1, score2); // Debug

        // Actualizar avatares
        updatePlayerAvatar('.player-column:first-child .player-avatar', player1);
        updatePlayerAvatar('.player-column:last-child .player-avatar', player2);

        // Aplicar estilos de ganador/perdedor
        const player1Result = document.querySelector('.player-column:first-child .player-result');
        const player2Result = document.querySelector('.player-column:last-child .player-result');
        
        if (winner === player1.username) {
            player1Result.classList.add('winner');
            player2Result.classList.add('loser');
        } else {
            player2Result.classList.add('winner');
            player1Result.classList.add('loser');
        }

        // Configurar botones
        requiredElements.returnButton.onclick = () => window.location.href = '/game';
        requiredElements.playAgainButton.onclick = () => window.location.reload();

        // Mostrar modal
        gameOverScreen.style.display = 'flex';
        gameOverScreen.style.opacity = '1';
        gameOverScreen.style.visibility = 'visible';
    } catch (error) {
        console.error('Error al actualizar el modal:', error);
        console.error('Scores recibidos:', scores); // Debug adicional
    }
}

function updatePlayerAvatar(selector, player) {
    const avatarContainer = document.querySelector(selector);
    if (avatarContainer) {
        if (player.profile_image) {
            avatarContainer.innerHTML = `<img src="${player.profile_image}" alt="${player.username}" />`;
        } else if (player.fortytwo_image) {
            avatarContainer.innerHTML = `<img src="${player.fortytwo_image}" alt="${player.username}" />`;
        } else if (player.is_cpu) {
            avatarContainer.innerHTML = '<i class="fas fa-robot"></i>';
        } else {
            avatarContainer.innerHTML = '<i class="fas fa-user"></i>';
        }
    }
}

export function hideGameOverModal() {
    const gameOverScreen = document.getElementById('gameOverScreen');
    if (gameOverScreen) {
        gameOverScreen.style.display = 'none';
    }
}
