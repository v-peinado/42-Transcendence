export function showGameOverModal(winner, player1, player2, scores, isTournament = false) {
    const gameOverScreen = document.getElementById('gameOverScreen');
    if (!gameOverScreen) {
        console.error('Modal de game over no encontrado');
        return;
    }

    // Elementos esenciales (siempre requeridos)
    const requiredElements = {
        winnerText: document.getElementById('winnerText'),
        finalPlayer1Name: document.getElementById('finalPlayer1Name'),
        finalPlayer2Name: document.getElementById('finalPlayer2Name'),
        player1Score: document.querySelector('.player1-score'),
        player2Score: document.querySelector('.player2-score'),
        returnToLobby: document.getElementById('returnToLobby') // Cambiar returnButton por returnToLobby
    };

    // Verificar solo los elementos esenciales
    for (const [key, element] of Object.entries(requiredElements)) {
        if (!element) {
            console.error(`Elemento esencial ${key} no encontrado en el modal`);
            return;
        }
    }

    // Elementos opcionales
    const playAgainButton = document.getElementById('playAgain');
    
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
        requiredElements.returnToLobby.onclick = () => window.location.href = '/game'; // Cambiar returnButton por returnToLobby
        if (playAgainButton) {
            playAgainButton.style.display = 'none'; // Ocultarlo en matchmaking
        }

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
        // Prioridad: 1. Foto de perfil, 2. Foto de 42, 3. Avatar generado
        const avatarUrl = player.profile_image || 
                         player.fortytwo_image || 
                         `https://api.dicebear.com/7.x/avataaars/svg?seed=${player.username}`;

        avatarContainer.innerHTML = `
            <img src="${avatarUrl}" 
                 alt="${player.username}" 
                 class="avatar-img"
                 onerror="this.src='https://api.dicebear.com/7.x/avataaars/svg?seed=${player.username}'"/>`;
    }
}

export function hideGameOverModal() {
    const gameOverScreen = document.getElementById('gameOverScreen');
    if (gameOverScreen) {
        gameOverScreen.style.display = 'none';
    }
}
