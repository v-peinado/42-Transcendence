import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js'; // Añadir esta importación
import { gameReconnectionService } from '../../services/GameReconnectionService.js';
import { showGameOverModal, hideGameOverModal } from '../../components/GameOverModal.js';
import { matchFoundModalService } from '../../services/MatchFoundModalService.js';

export async function GameMatchView(gameId) {
    console.log('Iniciando partida:', gameId);

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
	
    const app = document.getElementById('app');
    
    // Cargar navbar autenticado y template del juego
    const [template, modalTemplate, userInfo] = await Promise.all([
        loadHTML('/views/game/templates/GameMatch.html'),
        loadHTML('/views/game/templates/modals/GameOverModal.html'),
        AuthService.getUserProfile()
    ]);

	// Si no pudimos obtener el perfil del usuario, redirigir al login
	if (!userInfo || userInfo.error) {
		console.error('GameMatchView: No se pudo cargar el perfil del usuario');
		localStorage.removeItem('isAuthenticated');
		window.location.href = '/login?redirect=/game/' + gameId;
		return;
	}

    // Obtener el navbar procesado y añadirlo
    const navbarHtml = await getNavbarHTML(true, userInfo);
    
    // Preparar el contenido
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template;
    
    // Limpiar y añadir el nuevo contenido con navbar
    app.innerHTML = navbarHtml;
    app.appendChild(tempDiv.firstElementChild);

    // Añadir el modal al contenedor
    const modalsContainer = document.getElementById('modalsContainer');
    if (modalsContainer) {
        modalsContainer.innerHTML = modalTemplate;
        // Asegurarnos que está oculto
        const gameOverScreen = document.getElementById('gameOverScreen');
        if (gameOverScreen) {
            gameOverScreen.style.display = 'none';
        }
    }

    // Variables de estado
    let playerSide = null;
    let gameState = null;
    let activeKeys = new Set();
    let movementInterval = null;
    const userId = localStorage.getItem('user_id');
    
    // Añadir una variable para rastrear la última notificación de reconexión
	let lastReconnectNotification = 0;

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

								 // Guardar IDs de los jugadores
								document.querySelector('#leftPlayerName').dataset.playerId = data.player1_id;
								document.querySelector('#rightPlayerName').dataset.playerId = data.player2_id;

								// Configurar controles inmediatamente
								setupControls();
							}
						}
						break;

					case 'game_start':
						console.log('Iniciando juego:', data);
						// Actualizar nombres en todos los lugares necesarios
						document.querySelector('#player1NamePreMatch').textContent = data.player1;
						document.querySelector('#player2NamePreMatch').textContent = data.player2;
						document.querySelector('#leftPlayerName').textContent = data.player1;
						document.querySelector('#rightPlayerName').textContent = data.player2;

						// Asignar lado del jugador
						if (userId === data.player1_id.toString()) {
							playerSide = 'left';
						} else if (userId === data.player2_id.toString()) {
							playerSide = 'right';
						}

						// Guardar datos para posible reconexión
						gameReconnectionService.saveGameData(gameId, {
							playerSide,
							player1: data.player1,
							player2: data.player2,
							player1_id: data.player1_id,
							player2_id: data.player2_id
						});

						// Guardar IDs de los jugadores
						document.querySelector('#leftPlayerName').dataset.playerId = data.player1_id;
						document.querySelector('#rightPlayerName').dataset.playerId = data.player2_id;

						showPreMatchSequence(data.player1, data.player2, playerSide).then(() => {
							setupControls();
						});
						break;

					case 'game_state':
						handleGameState(data.state);
						break;

					case 'game_finished':
						handleGameEnd(data);
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

					case 'chat_message':
						handleChatMessage(data);
						// También mostrar una notificación discreta si no es del usuario actual
						if (data.sender_id.toString() !== userId) {
							showGameNotification(
								`Mensaje de ${data.sender}`,
								'info',
								'fa-comment'
							);
						}
						break;
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

				// Evitar mostrar múltiples notificaciones en un período corto de tiempo
				const now = Date.now();
				if (now - lastReconnectNotification > 3000) { // Solo una notificación cada 3 segundos
					showGameNotification('¡Reconectado al juego!', 'success');
					lastReconnectNotification = now;
				}

			// Reiniciar los controles explícitamente tras reconexión
			if (playerSide) {
				activeKeys.clear(); // Limpiar estado de teclas
				setupControls(); // Reconfigurar controles
				}
			},
			onReconnectFailed: () => {
				document.getElementById('gameStatus').textContent = '❌ No se pudo reconectar';
				showGameNotification('No se pudo reconectar. Intenta refrescar la página.', 'error');
			}
		});

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
				}, 300); // Tiempo para que termine la animación de salida
			}, 3000);
		}

		async function showPreMatchSequence(player1, player2, playerSide) {
			return new Promise(async (resolve) => {
				try {
					// Obtener los IDs de los jugadores
					const opponentId = playerSide === 'left' ? 
						document.querySelector('#rightPlayerName').dataset.playerId : 
						document.querySelector('#leftPlayerName').dataset.playerId;

					// Obtener stats del oponente
					const opponentResponse = await fetch(`/api/dashboard/player-stats-id/${opponentId}/`, {
						method: 'GET',
						headers: { 'Content-Type': 'application/json' },
						credentials: 'include'
					});

					let opponentData = null;
					if (opponentResponse.ok) {
						opponentData = await opponentResponse.json();
					}

					// Mostrar el modal con la información correcta según el lado
					await matchFoundModalService.showMatchFoundModal(
						// El primer jugador (izquierda) siempre es player1
						{
							username: player1,
							profile_image: playerSide === 'left' ? userInfo.profile_image : opponentData?.stats.profile_image,
							fortytwo_image: playerSide === 'left' ? userInfo.fortytwo_image : opponentData?.stats.fortytwo_image,
							avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${player1}`
						},
						// El segundo jugador (derecha) siempre es player2
						{
							username: player2,
							profile_image: playerSide === 'right' ? userInfo.profile_image : opponentData?.stats.profile_image,
							fortytwo_image: playerSide === 'right' ? userInfo.fortytwo_image : opponentData?.stats.fortytwo_image,
							avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${player2}`
						},
						playerSide // Pasamos solo el lado del jugador, sin texto predefinido
					);

					// Decimos al servidor que estamos listos para la cuenta atrás
					gameReconnectionService.send({
						type: 'ready_for_countdown'
					});

					resolve();
				} catch (error) {
					console.error('Error al obtener información del oponente:', error);
					// Fallback con información básica
					await matchFoundModalService.showMatchFoundModal(
						{
							username: player1,
							avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${player1}`
						},
						{
							username: player2,
							avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${player2}`
						},
						playerSide === 'left' ? 'W / S' : '↑ / ↓'
					);
					resolve();
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

    async function handleGameEnd(data) {
        try {
            // Usar los IDs que recibimos en game_info o game_start
            const player1Id = document.querySelector('#leftPlayerName').dataset.playerId;
            const player2Id = document.querySelector('#rightPlayerName').dataset.playerId;
            const opponentId = playerSide === 'left' ? player2Id : player1Id;

            if (!opponentId) {
                console.error('No se pudo obtener el ID del oponente');
                // Mostrar modal con datos básicos...
                return;
            }

            // Obtener stats del oponente
            const opponentResponse = await fetch(`/api/dashboard/player-stats-id/${opponentId}/`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });

            if (!opponentResponse.ok) {
                throw new Error(`Error al obtener stats: ${opponentResponse.status}`);
            }

            const opponentData = await opponentResponse.json();

            showGameOverModal(
                data.winner_username,
                playerSide === 'left' ? 
                    {
                        username: userInfo.username,
                        profile_image: userInfo.profile_image,
                        fortytwo_image: userInfo.fortytwo_image,
                        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`
                    } : 
                    {
                        username: opponentData.stats.username,
                        profile_image: opponentData.stats.profile_image,
                        fortytwo_image: opponentData.stats.fortytwo_image,
                        avatar: opponentData.stats.avatar
                    },
                playerSide === 'right' ? 
                    {
                        username: userInfo.username,
                        profile_image: userInfo.profile_image,
                        fortytwo_image: userInfo.fortytwo_image,
                        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`
                    } : 
                    {
                        username: opponentData.stats.username,
                        profile_image: opponentData.stats.profile_image,
                        fortytwo_image: opponentData.stats.fortytwo_image,
                        avatar: opponentData.stats.avatar
                    },
                {
                    player1: data.final_score.left,
                    player2: data.final_score.right
                },
                false
            );
        } catch (error) {
            console.error('Error al obtener información del oponente:', error);
            // Mostrar modal con información básica en caso de error
            showGameOverModal(
                data.winner_username,
                playerSide === 'left' ? 
                    {
                        username: userInfo.username,
                        profile_image: userInfo.profile_image,
                        fortytwo_image: userInfo.fortytwo_image,
                        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`
                    } : 
                    {
                        username: data.player2_username,
                        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${data.player2_username}`
                    },
                playerSide === 'right' ? 
                    {
                        username: userInfo.username,
                        profile_image: userInfo.profile_image,
                        fortytwo_image: userInfo.fortytwo_image,
                        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo.username}`
                    } : 
                    {
                        username: data.player1_username,
                        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${data.player1_username}`
                    },
                {
                    player1: data.final_score.left,
                    player2: data.final_score.right
                },
                false
            );
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
		// No procesar si el foco está en un input (para que el chat u otros campos funcionen)
		if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

		// No procesar si no tenemos un lado asignado
		if (!playerSide) return;

		// Permitir teclas durante el juego activo y también durante la cuenta atrás
		if (!gameState || (gameState.status !== 'playing' && gameState.status !== 'countdown')) return;

		const key = e.key.toLowerCase();
		const isValidKey = (playerSide === 'left' && (key === 'w' || key === 's')) ||
			(playerSide === 'right' && (key === 'arrowup' || key === 'arrowdown'));

		if (!isValidKey) return;

		e.preventDefault();
		activeKeys.add(key);
	}

    function handleKeyUp(e) {
		const key = e.key.toLowerCase();
		activeKeys.delete(key);

		// No procesar más si no tenemos un lado asignado
		if (!playerSide) return;

		// Determinar si es una tecla de movimiento para este jugador
		const isMovementKey = (playerSide === 'left' && (key === 'w' || key === 's')) ||
			(playerSide === 'right' && (key === 'arrowup' || key === 'arrowdown'));

		// Si se soltó una tecla de movimiento o no quedan teclas activas, enviar comando
		if (isMovementKey || activeKeys.size === 0) {
			// Verificar direcciones restantes
			const remainingDirection = getDirection();

			// Enviar comando de dirección
			const message = {
				type: 'move_paddle',
				direction: remainingDirection,
				side: playerSide,
				player_id: parseInt(userId),
				timestamp: Date.now(),
				force_stop: remainingDirection === 0 // Forzar parada si no hay más dirección
			};
			gameReconnectionService.send(message);
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

		// Limpiar estado y controladores antiguos si existen
		activeKeys.clear();
		if (movementInterval) {
			clearInterval(movementInterval);
		}
		document.removeEventListener('keydown', handleKeyDown);
		document.removeEventListener('keyup', handleKeyUp);
		
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
        if (!document.fullscreenElement && !document.webkitFullscreenElement &&
            !document.mozFullScreenElement && !document.msFullscreenElement) {
            gameWrapper.classList.remove('fullscreen');
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    // Cleanup mejorado
    return () => {
        if (movementInterval) {
            clearInterval(movementInterval);
        }
        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('keyup', handleKeyUp);

		// Usar el servicio para desconectar WebSocket
		gameReconnectionService.disconnect();

        document.removeEventListener('fullscreenchange', handleFullscreenChange);
        document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
        document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
    };
}