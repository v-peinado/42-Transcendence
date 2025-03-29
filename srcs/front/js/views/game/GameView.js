import { gameWebSocketService } from '../../services/GameWebSocketService.js';
import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';
import { ChatWidget } from '../../components/ChatWidget.js';
import { initializeMenuAnimations } from './GameMenuAnimations.js';
import { GameThemes, getThemeIcon } from './components/GameThemes.js';
import { ThemePreview } from './components/ThemePreview.js';

export default async function GameView(userInfo = null) {
    const app = document.getElementById('app');
    const [template, navbarHtml, footerHtml] = await Promise.all([
        loadHTML('/views/game/templates/GameMenu.html'),
        loadHTML('/views/components/NavbarAuthenticated.html'),
        loadHTML('/views/components/Footer.html')
    ]);

    app.innerHTML = navbarHtml + template + footerHtml;

    // Actualizar la información del usuario en el navbar
    if (userInfo) {
        const navElement = document.querySelector('nav');
        if (navElement) {
            const profileImage = userInfo?.profile_image || 
                               userInfo?.fortytwo_image || 
                               `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;

            navElement.querySelectorAll('#nav-profile-image, #nav-profile-image-large').forEach(img => {
                img.src = profileImage;
                img.onerror = () => img.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;
            });

            navElement.querySelectorAll('#nav-username, #nav-username-large').forEach(el => {
                el.textContent = userInfo.username;
            });
        }

        const usernameElement = document.getElementById('username-placeholder');
        if (usernameElement) {
            usernameElement.textContent = userInfo.username;
        }
    }

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

        // Añadir el manejo del botón de personalización
        const customizeBtn = document.getElementById('customizeGameBtn');
        if (customizeBtn) {
            customizeBtn.addEventListener('click', () => {
                const pauseMenu = document.createElement('div');
                pauseMenu.id = 'themeMenu';
                pauseMenu.className = 'game-pause-modal';
                
                const themeButtons = Object.entries(GameThemes).map(([key, theme]) => `
                    <button data-theme="${key}" class="game-theme-btn ${localStorage.getItem('pongTheme') === JSON.stringify(theme) ? 'active' : ''}">
                        <i class="fas ${getThemeIcon(key)}"></i>
                        <span>${theme.name}</span>
                    </button>
                `).join('');

                pauseMenu.innerHTML = `
                    <div class="game-pause-content">
                        <div class="game-pause-header">
                            <h2 class="game-pause-title">
                                <i class="fas fa-paint-brush me-2"></i>
                                Personaliza tu juego
                            </h2>
                        </div>
                        
                        <div class="preview-container">
                            <div class="preview-title">Vista previa del tema</div>
                            <canvas id="themePreviewCanvas" class="game-theme-preview"></canvas>
                        </div>

                        <div class="game-theme-selector">
                            ${themeButtons}
                        </div>
                        
                        <div class="game-pause-actions">
                            <button class="game-pause-resume-btn">
                                <i class="fas fa-check me-2"></i>Aceptar
                            </button>
                        </div>
                    </div>
                `;

                document.body.appendChild(pauseMenu);
                
                // Inicializar el preview después de añadir el modal al DOM
                const previewCanvas = document.getElementById('themePreviewCanvas');
                // Obtener el tema actual o usar el clásico por defecto
                const currentTheme = GameThemes[localStorage.getItem('currentTheme') || 'classic'];
                const preview = new ThemePreview(previewCanvas, currentTheme);

                // Manejar cambios de tema
                pauseMenu.querySelectorAll('.game-theme-btn').forEach(btn => {
                    btn.onclick = () => {
                        const themeKey = btn.dataset.theme;
                        const newTheme = GameThemes[themeKey];
                        preview.updateTheme(newTheme);
                        
                        // Guardar el tema de la misma forma que en BaseGame
                        localStorage.setItem('pongTheme', JSON.stringify(newTheme));
                        
                        // También mantener el themeKey para consistencia
                        localStorage.setItem('currentTheme', themeKey);
                        
                        // Emitir el evento con el tema completo
                        document.dispatchEvent(new CustomEvent('themeChanged', {
                            detail: { theme: newTheme }
                        }));
                        
                        // Actualizar clases active
                        pauseMenu.querySelectorAll('.game-theme-btn').forEach(b => 
                            b.classList.remove('active')
                        );
                        btn.classList.add('active');
                    };
                });

                // Simplificar el botón de aceptar para que solo cierre el modal
                const resumeBtn = pauseMenu.querySelector('.game-pause-resume-btn');
                if (resumeBtn) {
                    resumeBtn.onclick = () => pauseMenu.remove();
                }
            });
        }

        // Inicializar animaciones después de renderizar
        initializeMenuAnimations();
    }, 0);

    // Cleanup
    return () => {
        gameWebSocketService.disconnect();
        // No necesitamos limpiar el ChatWidget ya que es un singleton
    };
}
