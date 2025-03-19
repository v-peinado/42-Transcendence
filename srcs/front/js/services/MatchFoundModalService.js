class MatchFoundModalService {
    updatePlayerAvatar(selector, player) {
        const avatarContainer = document.querySelector(selector);
        if (avatarContainer) {
            // Misma lógica que en GameOverModal: priorizar la imagen de 42
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

    async showMatchFoundModal(player1Info, player2Info, playerSide) {
        return new Promise(async (resolve) => {
            const modal = document.getElementById('matchFoundModal');
            const countdown = document.getElementById('countdown');

            // Actualizar información de jugadores
            document.getElementById('player1NamePreMatch').textContent = player1Info.username;
            document.getElementById('player2NamePreMatch').textContent = player2Info.username;
            
            // Mostrar los controles según el lado del jugador
            document.getElementById('playerControls').textContent = 
                playerSide === 'left' ? 'W / S' : '↑ / ↓';

            // Actualizar avatares
            this.updatePlayerAvatar('#player1Avatar', player1Info);
            this.updatePlayerAvatar('#player2Avatar', player2Info);

            // Mostrar modal
            modal.style.display = 'flex';
            await new Promise(r => setTimeout(r, 2000));

            // Ocultar modal con animación
            modal.style.animation = 'fadeOut 0.5s ease-out';
            await new Promise(r => setTimeout(r, 500));
            modal.style.display = 'none';

            // Preparar countdown
            countdown.style.display = 'flex';
            countdown.textContent = '';

            resolve();
        });
    }

    hideMatchFoundModal() {
        const modal = document.getElementById('matchFoundModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

export const matchFoundModalService = new MatchFoundModalService();
