import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js'; // Añadir esta importación
import { showGameOverModal } from '../../components/GameOverModal.js';
import { gameReconnectionService } from '../../services/GameReconnectionService.js';

export async function GameMatchView(gameId) {
    // Validar que tenemos un gameId válido
    if (!gameId || isNaN(parseInt(gameId))) {
        console.error('GameMatchView: ID de partida inválido');
        window.history.pushState(null, null, '/404');
        const NotFoundView = (await import('../NotFoundView.js')).NotFoundView;
        await NotFoundView();
        return;
    }

    // Asegurarnos que estamos autenticados
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    if (!isAuthenticated) {
        console.error('GameMatchView: Usuario no autenticado');
        window.location.href = '/login?redirect=/game/' + gameId;
        return;
    }

    // Verificar si la partida existe y el usuario tiene acceso
    try {
        console.log('Verificando acceso a partida:', gameId);
        const gameAccess = await GameService.verifyGameAccess(gameId);

        if (!gameAccess.exists || !gameAccess.can_access) {
            console.error('GameMatchView: Acceso a partida denegado:', gameAccess.message);
            window.history.pushState(null, null, '/404');
            const NotFoundView = (await import('../NotFoundView.js')).NotFoundView;
            await NotFoundView();
            return;
        }
    } catch (error) {
        console.error('Error verificando acceso a partida:', error);
    }

    console.log('Iniciando partida:', gameId);
    const app = document.getElementById('app');
    
    // Cargar navbar autenticado y template del juego
    const [template, userInfo] = await Promise.all([
        loadHTML('/views/game/templates/GameMatch.html'),
        AuthService.getUserProfile()
    ]);

    // Obtener el navbar procesado y añadirlo
    const navbarHtml = await getNavbarHTML(true, userInfo);
    
    // Preparar el contenido
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    
    // Limpiar y añadir el nuevo contenido con navbar
    app.innerHTML = navbarHtml;
    app.appendChild(tempDiv.firstElementChild);

    // Cargar CSS
    if (!document.querySelector('link[href="/css/game.css"]')) {
        const linkElem = document.createElement('link');
        linkElem.rel = 'stylesheet';
        linkElem.href = '/css/game.css';
        document.head.appendChild(linkElem);
    }

    // Variables de estado
    let playerSide = null;
    let gameState = null;
    let activeKeys = new Set();
    let movementInterval = null;
    const userId = localStorage.getItem('user_id');
    
    console.log('User ID en juego:', userId);  // Debug user_id

    // Setup canvas y contexto
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 1000;
    canvas.height = 600;

    // Establecer conexión WebSocket usando el servicio de reconexión
    const socket = gameReconnectionService.setupConnection(gameId, {
        onOpen: (reconnecting) => {
            console.log(`Conexión WebSocket abierta. Reconectando: ${reconnecting}`);
            const gameStatus = document.getElementById('gameStatus');
            if (gameStatus) {
                gameStatus.textContent = reconnecting ?
                    '🔄 Reconectando a la partida...' : '🎮 Conectado - Esperando oponente...';
            }
        },
        onMessage: (data) => {
            switch (data.type) {
                case 'game_info':
                    console.log('Recibida información del juego:', data);
                    if (!playerSide && userId) {
                        if (userId === data.player1_id.toString()) {
                            playerSide = 'left';
                        } else if (userId === data.player2_id.toString()) {
                            playerSide = 'right';
                        }

                        if (playerSide) {
                            console.log('Lado del jugador determinado:', playerSide);
                            gameReconnectionService.saveGameData(gameId, {
                                playerSide,
                                player1: data.player1,
                                player2: data.player2,
                                player1_id: data.player1_id,
                                player2_id: data.player2_id
                            });

                            // Actualizar nombres si están disponibles
                            document.querySelector('#leftPlayerName').textContent = data.player1;
                            document.querySelector('#rightPlayerName').textContent = data.player2;

                            // Configurar controles inmediatamente
                            setupControls();
                        }
                    }
                    break;

                case 'player_disconnected':
                    showGameNotification(
                        `${data.username || 'Jugador'} se ha desconectado temporalmente`,
                        'warning',
                        'fa-user-slash'
                    );
                    break;

                case 'player_reconnected':
                    showGameNotification(
                        `¡${data.username || 'Jugador'} ha vuelto a la partida!`,
                        'success',
                        'fa-user-check'
                    );
                    break;

                // ...existing switch cases...
            }
        },
        onDisconnect: (attempt, max) => {
            document.getElementById('gameStatus').textContent =
                `🔄 Conexión perdida. Reintentando... (${attempt}/${max})`;
        },
        onReconnect: () => {
            const gameStatus = document.getElementById('gameStatus');
            if (gameStatus) {
                gameStatus.textContent = '🎮 Reconectado!';
            }
            showGameNotification('¡Reconectado al juego!', 'success');
        },
        onReconnectFailed: () => {
            document.getElementById('gameStatus').textContent = '❌ No se pudo reconectar';
            showGameNotification('No se pudo reconectar. Intenta refrescar la página.', 'error');
        }
    });

    async function showPreMatchSequence(player1, player2, playerSide) {
        return new Promise(async (resolve) => {
            const countdown = document.getElementById('countdown');
            if (countdown) {
                countdown.style.display = 'flex';
                countdown.textContent = '';
            }

            // Decimos al servidor que estamos listos para la cuenta atrás
            socket.send(JSON.stringify({
                type: 'ready_for_countdown'
            }));

            resolve();
        });
    }

    let gameStarted = false;
    let countdownShown = false;

    socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        console.log('Mensaje recibido en GameMatchView:', data);

        switch(data.type) {
            case 'game_start':
                console.log('Iniciando juego:', data);
                
                // Verificar elementos antes de actualizar
                const leftPlayerName = document.getElementById('leftPlayerName');
                const rightPlayerName = document.getElementById('rightPlayerName');

                if (leftPlayerName) leftPlayerName.textContent = data.player1;
                if (rightPlayerName) rightPlayerName.textContent = data.player2;

                // Asignar lado del jugador
                if (userId === data.player1_id.toString()) {
                    playerSide = 'left';
                } else if (userId === data.player2_id.toString()) {
                    playerSide = 'right';
                }

                await showPreMatchSequence(data.player1, data.player2, playerSide);
                setupControls();
                break;

            case 'game_state':
                if (!gameState) {
                    console.log('Inicializando estado del juego');
                    gameState = data.state;
                }
                handleGameState(data.state);
                break;
                
            case 'game_finished':
                handleGameEnd(data);
                break;
        }
    };

    async function handleGameStart(data) {
        console.log('Game Start:', {
            player1_id: data.player1_id,
            player2_id: data.player2_id,
            myId: userId
        });

        // Actualizar avatares y nombres solo si existen los elementos
        const player1Avatar = document.querySelector('.player-card:first-child .player-avatar');
        const player2Avatar = document.querySelector('.player-card:last-child .player-avatar');
        const playerInfo = document.getElementById('playerInfo');
        const controlsInfo = document.getElementById('controlsInfo');

        // Actualizar información basada en el lado del jugador
        if (userId === data.player1_id.toString()) {
            playerSide = 'left';
            if (playerInfo) playerInfo.textContent = `Tú eres el Jugador 1 (${data.player1})`;
            if (controlsInfo) controlsInfo.textContent = 'Controles: W/S para arriba/abajo';
        } else if (userId === data.player2_id.toString()) {
            playerSide = 'right';
            if (playerInfo) playerInfo.textContent = `Tú eres el Jugador 2 (${data.player2})`;
            if (controlsInfo) controlsInfo.textContent = 'Controles: ↑/↓ para arriba/abajo';
        }

        // Actualizar avatares si existen los elementos y la información
        updateAvatars(data.player1_info, data.player2_info);
    }

    // Nueva función para manejar la actualización de avatares
    function updateAvatars(player1Info, player2Info) {
        const avatarSelectors = {
            player1: '.player-card:first-child .player-avatar',
            player2: '.player-card:last-child .player-avatar',
            finalPlayer1: '.player-column:first-child .player-avatar',
            finalPlayer2: '.player-column:last-child .player-avatar'
        };

        Object.entries(avatarSelectors).forEach(([player, selector]) => {
            const avatarContainer = document.querySelector(selector);
            const info = player.includes('player1') ? player1Info : player2Info;
            
            if (avatarContainer && info) {
                if (info.profile_image) {
                    avatarContainer.innerHTML = `<img src="${info.profile_image}" alt="Avatar" />`;
                } else if (info.fortytwo_image) {
                    avatarContainer.innerHTML = `<img src="${info.fortytwo_image}" alt="Avatar" />`;
                }
            }
        });
    }

    function handleGameState(state) {
        if (!state) return;
        
        gameState = state;
        
		// Si hay una cuenta atrás en el estado, actualizar la UI de cuenta atrás
		if (state.countdown !== undefined) {
			const countdown = document.getElementById('countdown');
			countdown.style.display = 'flex';
			countdown.textContent = state.countdown === "GO!" ? "GO!" : state.countdown.toString();
			countdown.classList.remove('countdown-pulse');
			void countdown.offsetWidth; // Forzar reflow
			countdown.classList.add('countdown-pulse');
	
			// Reproducir sonido solo si viene con el indicador
			if (state.play_sound) {
				soundService.playCountdown();
			}
		} else if (state.status === 'playing') {
			// Si el estado es playing y ya no hay cuenta atrás, ocultar el elemento de cuenta atrás
			document.getElementById('countdown').style.display = 'none';
		}
	
        // Actualizar marcador si existe
        const leftScore = document.querySelector('.minimal-header .player-score:first-child');
        const rightScore = document.querySelector('.minimal-header .player-score:last-child');
        if (leftScore && rightScore) {
            leftScore.textContent = state.paddles.left.score || '0';
            rightScore.textContent = state.paddles.right.score || '0';
        }

        // Dibujar el estado del juego
        drawGame();
    }

    function drawGame() {
        if (!gameState || !ctx) return;

        // Limpiar canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Fondo
        ctx.fillStyle = 'rgba(16, 19, 34, 0.95)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Línea central
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.setLineDash([10, 10]);
        ctx.beginPath();
        ctx.moveTo(canvas.width / 2, 0);
        ctx.lineTo(canvas.width / 2, canvas.height);
        ctx.stroke();
        ctx.setLineDash([]);

        // Dibujar palas
        ctx.fillStyle = 'white';
        Object.values(gameState.paddles).forEach(paddle => {
            ctx.fillRect(paddle.x, paddle.y, paddle.width, paddle.height);
        });

        // Dibujar pelota
        if (gameState.ball) {
            ctx.beginPath();
            ctx.arc(gameState.ball.x, gameState.ball.y, gameState.ball.radius || 5, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function handleGameEnd(data) {
        const player1 = {
            username: data.final_score?.player1_name || 'Jugador 1',
            ...data.final_score?.player1_info
        };

        const player2 = {
            username: data.final_score?.player2_name || 'Jugador 2',
            ...data.final_score?.player2_info
        };

        showGameOverModal(
            data.winner,
            player1,
            player2,
            {
                player1: data.final_score?.player1 || 0,
                player2: data.final_score?.player2 || 0
            }
        );
        
        if (data.winner === playerSide) {
            soundService.playVictory();
        } else {
            soundService.playDefeat();
        }
    }

    function animateScore(element, finalScore) {
        let start = 0;
        const duration = 1000;
        const startTime = performance.now();
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(progress * finalScore);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }

    function handleKeyDown(e) {
        e.preventDefault();
        if (!playerSide) return;

        const key = e.key.toLowerCase();
        const isValidKey = (playerSide === 'left' && (key === 'w' || key === 's')) ||
                          (playerSide === 'right' && (key === 'arrowup' || key === 'arrowdown'));
        
        if (!isValidKey) return;

        activeKeys.add(key);
        // No enviamos mensaje aquí, el intervalo se encarga
    }

    function handleKeyUp(e) {
        const key = e.key.toLowerCase();
        activeKeys.delete(key);

        // Si no hay teclas activas, enviar dirección 0
        if (activeKeys.size === 0) {
            const message = {
                type: 'move_paddle',
                direction: 0,
                side: playerSide,
                player_id: parseInt(userId)
            };
            socket.send(JSON.stringify(message));
        }
    }

    function getDirection() {
        if (playerSide === 'left') {
            if (activeKeys.has('w')) return -1;
            if (activeKeys.has('s')) return 1;
        } else {
            if (activeKeys.has('arrowup')) return -1;
            if (activeKeys.has('arrowdown')) return 1;
        }
        return 0;
    }

    function setupControls() {
        console.log('Configurando controles para lado:', playerSide);
        // Iniciar el intervalo de movimiento continuo
        movementInterval = setInterval(() => {
            if (activeKeys.size > 0) {
                const direction = getDirection();
                const message = {
                    type: 'move_paddle',
                    direction: direction,
                    side: playerSide,
                    player_id: parseInt(userId)
                };
                socket.send(JSON.stringify(message));
            }
        }, 16);  // ~60 FPS

        document.addEventListener('keydown', handleKeyDown);
        document.addEventListener('keyup', handleKeyUp);
    }

    // Añadir después de la configuración inicial
    const gameWrapper = document.querySelector('.game-wrapper');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            if (gameWrapper.requestFullscreen) {
                gameWrapper.requestFullscreen();
            } else if (gameWrapper.webkitRequestFullscreen) {
                gameWrapper.webkitRequestFullscreen();
            } else if (gameWrapper.msRequestFullscreen) {
                gameWrapper.msRequestFullscreen();
            }
            gameWrapper.classList.add('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            gameWrapper.classList.remove('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    });

    // Manejar cambios de pantalla completa
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    function handleFullscreenChange() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement && !document.msFullscreenElement) {
            gameWrapper.classList.remove('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    // Verificar que todos los elementos críticos existen
    const criticalElements = {
        gameCanvas: document.getElementById('gameCanvas'),
        gameOverScreen: document.getElementById('gameOverScreen'),
        leftPlayerName: document.getElementById('leftPlayerName'),
        rightPlayerName: document.getElementById('rightPlayerName')
    };

    for (const [name, element] of Object.entries(criticalElements)) {
        if (!element) {
            console.error(`Elemento crítico no encontrado: ${name}`);
            // Podrías mostrar un mensaje de error al usuario aquí
        }
    }

    // Cleanup mejorado
    return () => {
        if (movementInterval) {
            clearInterval(movementInterval);
            movementInterval = null;
        }

        const cssLink = document.querySelector('link[href="/css/game.css"]');
        if (cssLink) {
            document.head.removeChild(cssLink);
        }

        document.removeEventListener('fullscreenchange', handleFullscreenChange);
        document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
        document.removeEventListener('MSFullscreenChange', handleFullscreenChange);

        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('keyup', handleKeyUp);

        // Usar el servicio de reconexión para desconectar
        gameReconnectionService.disconnect();

        socket.close();
    };
}

// Función mejorada para mostrar notificaciones en el juego
function showGameNotification(message, type = 'info', iconClass = 'fa-info-circle') {
    const container = document.getElementById('gameNotificationsContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `game-notification ${type}`;

    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="notification-content">${message}</div>
    `;

    container.appendChild(notification);

    // Mostrar con un pequeño retraso para permitir la animación
    setTimeout(() => notification.classList.add('visible'), 10);

    // Auto-eliminar después de unos segundos
    setTimeout(() => {
        notification.classList.add('fadeout');
        setTimeout(() => {
            if (notification.parentNode === container) {
                container.removeChild(notification);
            }
        }, 300);
    }, 3000);
}