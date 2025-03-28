export function showGameOverModal(winner, player1, player2, scores, options = {}) {
    // Salir del modo pantalla completa si está activo
    if (document.fullscreenElement) {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }

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
        // Determinar el nombre del ganador basado en el username correcto
        const winnerName = winner === player1.username ? player1.username : player2.username;
        
        
        // Actualizar el texto del ganador
        requiredElements.winnerText.textContent = `¡${winnerName} ha ganado!`;
        
        // Actualizar nombres de jugadores
        if (requiredElements.finalPlayer1Name) {
            requiredElements.finalPlayer1Name.textContent = player1.username || 'Jugador 1';
        }
        if (requiredElements.finalPlayer2Name) {
            requiredElements.finalPlayer2Name.textContent = player2.username || 'Jugador 2';
        }
        
        // Actualizar puntuaciones
        if (requiredElements.player1Score) {
            requiredElements.player1Score.textContent = scores.player1;
        }
        if (requiredElements.player2Score) {
            requiredElements.player2Score.textContent = scores.player2;
        }

        // Actualizar avatares
        updatePlayerAvatar('.player-column:first-child', player1);
        updatePlayerAvatar('.player-column:last-child', player2);

        // Aplicar estilos de ganador/perdedor
        const player1Result = document.getElementById('player1Result');
        const player2Result = document.getElementById('player2Result');
        
        if (winnerName === player1.username) {
            player1Result?.classList.add('winner');
            player2Result?.classList.add('loser');
        } else {
            player2Result?.classList.add('winner');
            player1Result?.classList.add('loser');
        }

        // Configurar botones
        requiredElements.returnToLobby.onclick = () => window.location.href = '/game'; // Cambiar returnButton por returnToLobby
        if (playAgainButton) {
            playAgainButton.style.display = 'none'; // Ocultarlo en matchmaking
        }

        // Limpiar y actualizar la sección de botones
        const actionsContainer = document.querySelector('.game-over-screen .action-buttons');
        if (actionsContainer) {
            actionsContainer.innerHTML = '';
            
            // Verificar si hay botones personalizados y es un array
            if (options.customButtons && Array.isArray(options.customButtons)) {
                
                options.customButtons.forEach(btn => {
                    if (!btn || !btn.text || !btn.onClick) return;
                    
                    const button = document.createElement('button');
                    button.className = 'game-button primary d-flex align-items-center justify-content-center w-100 mb-3';
                    button.innerHTML = btn.text;
                    button.onclick = btn.onClick;
                    actionsContainer.appendChild(button);
                });
            } else {
                // Fallback a botón por defecto
                const defaultButton = document.createElement('button');
                defaultButton.className = 'game-button primary d-flex align-items-center justify-content-center w-100 mb-3';
                defaultButton.innerHTML = '<i class="fas fa-home me-2"></i>Volver al Menú';
                defaultButton.onclick = () => window.location.href = '/game';
                actionsContainer.appendChild(defaultButton);
            }
            
            // Añadir información de siguiente partida si existe
            if (options.nextMatch) {
                const nextMatchInfo = document.createElement('div');
                nextMatchInfo.className = 'next-match-info mt-3 text-center';
                nextMatchInfo.innerHTML = `
                    <h4 class="text-primary mb-2">Siguiente Partido</h4>
                    <p class="mb-0">${options.nextMatch}</p>
                `;
                actionsContainer.appendChild(nextMatchInfo);
            }
        }

        // Mostrar modal
        gameOverScreen.style.display = 'flex';
        gameOverScreen.style.opacity = '1';
        gameOverScreen.style.visibility = 'visible';
    } catch (error) {
        console.error('Error al actualizar el modal:', error);
        console.error('Datos recibidos:', { winner, player1, player2, scores, options }); // Debug adicional
    }
}

function updatePlayerAvatar(selector, player) {
    const avatarContainer = document.querySelector(`${selector} .go-avatar`);
    if (avatarContainer) {
        // Si es CPU, mostrar el icono del robot
        if (player.is_cpu) {
            avatarContainer.innerHTML = `<i class="fas fa-robot"></i>`;
            avatarContainer.closest('.player-column').setAttribute('data-player', 'cpu');
            return;
        }
        
        const avatarUrl = player.fortytwo_image || 
                         player.profile_image || 
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
