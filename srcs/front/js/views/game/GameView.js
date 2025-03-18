import { gameWebSocketService } from '../../services/GameWebSocketService.js';
import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { ChatWidget } from '../../components/ChatWidget.js';

export default async function GameView() {
    const app = document.getElementById('app');
    app.innerHTML = ''; // Limpiar el contenido anterior
    
    // Cargar y añadir el navbar autenticado
    const userInfo = await AuthService.getUserProfile();
    const navbarHtml = await getNavbarHTML(true, userInfo);
    const tempNavDiv = document.createElement('div');
    tempNavDiv.innerHTML = navbarHtml;
    app.appendChild(tempNavDiv.firstElementChild);
    
    // Cargar template del menú de juego
    const template = await loadHTML('/views/game/templates/GameMenu.html');
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    app.appendChild(tempDiv.firstElementChild);

    // Esperar al siguiente ciclo del event loop para asegurar que el DOM está actualizado
    setTimeout(async () => {
        // Obtener referencias a los elementos
        const elements = {
            matchmakingBtn: document.getElementById('matchmakingBtn'),
            aiBtn: document.getElementById('aiBtn'),
            localTournamentBtn: document.getElementById('localTournamentBtn'),
            onlineTournamentBtn: document.getElementById('onlineTournamentBtn'),
            friendBtn: document.getElementById('friendInviteBtn'),
            status: document.getElementById('status'),
            statusText: document.getElementById('status-text'),
            modal: document.getElementById('matchmakingModal'),
            modalStatusText: document.getElementById('modal-status-text'),
            cancelMatchmakingBtn: document.getElementById('cancelMatchmaking')
        };

        // Eliminar el código del timer
        const showMatchmakingModal = (show) => {
            if (show) {
                elements.modal.classList.add('show');
                elements.modal.style.display = 'flex';
            } else {
                elements.modal.classList.remove('show');
                elements.modal.style.display = 'none';
                localStorage.removeItem('matchmaking_active');
            }
            document.body.classList.toggle('matchmaking-modal-open', show);
        };

        // Verificar si hay una búsqueda activa al cargar
        const isSearchingActive = localStorage.getItem('matchmaking_active') === 'true';
        if (isSearchingActive) {
            showMatchmakingModal(true);
            elements.modalStatusText.textContent = 'Reconectando...';
            elements.matchmakingBtn.classList.add('disabled');
            
            // Reiniciar la conexión WebSocket
            gameWebSocketService.setupConnection((message) => {
                elements.modalStatusText.textContent = message;
            });
        }

        // Inicializar el chat widget inmediatamente después de verificar búsqueda activa
        if (!document.querySelector('.chat-widget-container')) {
            await ChatWidget.initialize();
        }

        // Event listeners para los modos de juego
        if (elements.matchmakingBtn) {
            elements.matchmakingBtn.addEventListener('click', async () => {
                try {
                    showMatchmakingModal(true);
                    elements.modalStatusText.textContent = 'Conectando al servidor...';
                    elements.matchmakingBtn.classList.add('disabled');

                    // Minimizar el chat widget cuando comience la búsqueda
                    const chatWidget = document.querySelector('.chat-widget');
                    const toggleBtn = document.querySelector('.chat-toggle-btn');
                    if (chatWidget && chatWidget.classList.contains('visible')) {
                        toggleBtn.click();
                    }

                    const userId = await AuthService.getUserId();
                    if (!userId) {
                        throw new Error('No se pudo obtener el ID del usuario');
                    }

                    await gameWebSocketService.setupConnection((message) => {
                        elements.modalStatusText.textContent = message;
                    });
                } catch (error) {
                    console.error('Error:', error);
                    elements.modalStatusText.textContent = `Error: ${error.message}`;
                    elements.matchmakingBtn.classList.remove('disabled');
                    setTimeout(() => showMatchmakingModal(false), 2000);
                }
            });
        }

        // Función global para cancelar matchmaking
        window.cancelMatchmaking = function() {
            console.log('Cancelando búsqueda (función global)');
            gameWebSocketService.disconnect();
            showMatchmakingModal(false);
            elements.matchmakingBtn.classList.remove('disabled');
            localStorage.removeItem('matchmaking_active');
        };

        // Solo por si acaso, mantener también el listener original
        document.getElementById('cancelMatchmaking').addEventListener('click', function(e) {
            console.log('Click en botón cancelar');
            e.preventDefault();
            e.stopPropagation();
            window.cancelMatchmaking();
        });

        // Event listener simplificado para el botón de cancelar
        document.getElementById('cancelMatchmaking').onclick = async function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Cancelando búsqueda...');
            
            try {
                await gameWebSocketService.disconnect();
                showMatchmakingModal(false);
                elements.matchmakingBtn.classList.remove('disabled');
                localStorage.removeItem('matchmaking_active');
            } catch (error) {
                console.error('Error al cancelar:', error);
                // Intentar limpiar el estado de todas formas
                showMatchmakingModal(false);
                elements.matchmakingBtn.classList.remove('disabled');
                localStorage.removeItem('matchmaking_active');
            }
        };

        // Event listeners para modos no disponibles
        const disabledModes = [
            elements.onlineTournamentBtn, 
            elements.friendBtn
        ].filter(btn => btn !== null); // Quitamos aiBtn y localTournamentBtn de la lista
        
        // Agregar listener específico para torneo local
        elements.localTournamentBtn.addEventListener('click', () => {
            window.location.href = '/tournament/local';
        });

        // Agregar listener para modo IA
        elements.aiBtn.addEventListener('click', () => {
            window.location.href = '/game/single-player';
        });
        elements.aiBtn.classList.remove('disabled'); // Habilitar el botón

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
    }, 0);

    // Cleanup
    return () => {
        gameWebSocketService.disconnect();
        // No necesitamos limpiar el ChatWidget ya que es un singleton
    };
}
