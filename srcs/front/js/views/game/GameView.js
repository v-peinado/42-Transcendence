import { gameWebSocketService } from '../../services/GameWebSocketService.js';
import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';

export default async function GameView() {
    const app = document.getElementById('app');
    
    // Cargar template del menú de juego
    const template = await loadHTML('/views/game/templates/GameMenu.html');
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    app.appendChild(tempDiv.firstElementChild);

    // Obtener referencias a los elementos
    const elements = {
        // Botones de modo de juego
        matchmakingBtn: document.getElementById('matchmakingBtn'),
        aiBtn: document.getElementById('aiBtn'),
        localTournamentBtn: document.getElementById('localTournamentBtn'),
        onlineTournamentBtn: document.getElementById('onlineTournamentBtn'),
        friendBtn: document.getElementById('friendBtn'),
        // Elementos de estado
        status: document.getElementById('status'),
        statusText: document.getElementById('status-text')
    };

    // Event listeners para los modos de juego
    elements.matchmakingBtn.addEventListener('click', async () => {
        try {
            elements.status.style.display = 'block';
            elements.statusText.textContent = 'Conectando al servidor...';
            elements.matchmakingBtn.classList.add('disabled');

            const userId = await AuthService.getUserId();
            if (!userId) {
                throw new Error('No se pudo obtener el ID del usuario');
            }

            await gameWebSocketService.setupConnection((message) => {
                elements.statusText.textContent = message;
            });
        } catch (error) {
            console.error('Error:', error);
            elements.statusText.textContent = `Error: ${error.message}`;
            elements.matchmakingBtn.classList.remove('disabled');
        }
    });

    // Event listeners para modos no disponibles
    const disabledModes = [elements.aiBtn, elements.localTournamentBtn, 
                          elements.onlineTournamentBtn, elements.friendBtn];
    
    disabledModes.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.status.style.display = 'block';
            elements.statusText.textContent = 'Modo no disponible aún';
            setTimeout(() => {
                elements.status.style.display = 'none';
            }, 2000);
        });
    });

    // Añadir efecto de brillo que sigue al cursor
    const cards = document.querySelectorAll('.game-mode-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / card.clientWidth) * 100;
            const y = ((e.clientY - rect.top) / card.clientHeight) * 100;
            card.style.setProperty('--x', `${x}%`);
            card.style.setProperty('--y', `${y}%`);
        });
    });

    // Cleanup
    return () => {
        gameWebSocketService.disconnect();
    };
}
