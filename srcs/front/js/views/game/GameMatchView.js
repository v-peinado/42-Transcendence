import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js'; // Añadir esta importación

export async function GameMatchView(gameId) {
    console.log('Iniciando partida:', gameId);

	// Validar que tenemos un gameId
	if (!gameId) {
		console.error('GameMatchView: No se proporcionó ID de partida');
		window.location.href = '/game';
		return;
	}

	// Asegurarnos que estamos autenticados
	const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
	if (!isAuthenticated) {
		console.error('GameMatchView: Usuario no autenticado');
		window.location.href = '/login?redirect=/game/' + gameId;
		return;
	}

    const app = document.getElementById('app');
    
    // Cargar navbar autenticado y template del juego
    const [template, userInfo] = await Promise.all([
        loadHTML('/views/game/templates/GameMatch.html'),
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
	let reconnecting = false;
	let socket = null;
    const userId = localStorage.getItem('user_id');
	const RECONNECT_INTERVAL = 2000; // Intentar reconectar cada 2 segundos
	let reconnectAttempts = 0;
	const MAX_RECONNECT_ATTEMPTS = 15; // 30 segundos (15 intentos x 2s)

	// Recuperar información de juego del localStorage (para reconexión)
	const savedGameData = localStorage.getItem(`game_${gameId}`);
	console.log('Datos guardados del juego:', savedGameData);

	if (savedGameData) {
		try {
			const gameData = JSON.parse(savedGameData);
			playerSide = gameData.playerSide;
			reconnecting = true;
			console.log('Recuperando datos de sesión anterior. Lado del jugador:', playerSide);

			// Actualizar UI con datos guardados si están disponibles
			if (gameData.player1 && gameData.player2) {
				setTimeout(() => {
					const leftName = document.querySelector('#leftPlayerName');
					const rightName = document.querySelector('#rightPlayerName');
					if (leftName && rightName) {
						leftName.textContent = gameData.player1;
						rightName.textContent = gameData.player2;
					}
				}, 100);
			}
		} catch (e) {
			console.error('Error al recuperar datos de juego guardados:', e);
		}
	}

    // Setup canvas y contexto
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 1000;
    canvas.height = 600;

	// Función para establecer conexión
	function setupConnection() {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws/game/${gameId}/`;
		console.log('Conectando a:', wsUrl, 'Reconectando:', reconnecting);

		// Cerrar socket existente si hubiera
		if (socket && socket.readyState !== WebSocket.CLOSED) {
			socket.close();
		}

		socket = new WebSocket(wsUrl);

		socket.onopen = () => {
			console.log('Conexión WebSocket establecida. Reconexión:', reconnecting, 'Lado:', playerSide);
			document.getElementById('gameStatus').textContent = reconnecting ?
				'🔄 Reconectando a la partida...' : '🎮 Conectado - Esperando oponente...';

			// Si estamos reconectando, solicitar estado actual del juego
			if (reconnecting) {
				console.log('Solicitando estado del juego al servidor...');
				setTimeout(() => {
					if (socket && socket.readyState === WebSocket.OPEN) {
						socket.send(JSON.stringify({
							type: 'request_game_state',
							player_id: parseInt(userId),
							game_id: parseInt(gameId)
						}));
						console.log('Solicitud de estado enviada');
					} else {
						console.error('Socket no disponible para enviar solicitud de estado');
					}
				}, 800); // Aumentar el delay para asegurar que el backend esté listo

				// Si ya sabemos nuestro lado, configurar controles inmediatamente
				if (playerSide) {
					console.log('Configurando controles para lado:', playerSide);
					setupControls();
				}
			}
		};

		socket.onclose = (event) => {
			console.log('Conexión cerrada', event);

			// Solo intentar reconectar si no fue un cierre controlado y el juego no ha terminado
			if (event.code !== 1000 && !document.getElementById('gameOverScreen').style.display === 'flex') {
				handleDisconnection();
			}
		};

		socket.onerror = (error) => {
			console.error('Error en WebSocket:', error);
			handleDisconnection();
		};

		socket.onmessage = async (event) => {
			const data = JSON.parse(event.data);
			console.log('Mensaje recibido en GameMatchView:', data);

			switch (data.type) {
				case 'game_info':
					// Mensaje adicional del servidor con información básica del juego
					console.log('Recibida información del juego:', data);
					if (!playerSide && userId) {
						if (userId === data.player1_id.toString()) {
							playerSide = 'left';
						} else if (userId === data.player2_id.toString()) {
							playerSide = 'right';
						}

						if (playerSide) {
							console.log('Lado del jugador determinado desde game_info:', playerSide);
							// Guardar información para futuras reconexiones
							saveGameData(gameId, {
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

					// Guardar datos del jugador para reconexión
					saveGameData(gameId, {
						playerSide,
						player1: data.player1,
						player2: data.player2,
						player1_id: data.player1_id,
						player2_id: data.player2_id
					});

					await showPreMatchSequence(data.player1, data.player2, playerSide);
					setupControls();
					break;

				case 'game_state':
					// Si es una reconexión, mostrar mensaje
					if (data.is_reconnection || reconnecting) {
						showReconnectionSuccess();
						reconnecting = false;
						reconnectAttempts = 0;

						// Si el servidor nos envía información del lado del jugador, usarla
						if (data.player_side) {
							playerSide = data.player_side;
							console.log('Lado del jugador recibido del servidor:', playerSide);

							// Guardar o actualizar datos
							const existingData = getSavedGameData(gameId) || {};
							saveGameData(gameId, {
								...existingData,
								playerSide: data.player_side
							});

							// Configurar controles si aún no están configurados
							if (!movementInterval) {
								setupControls();
							}
						}

						// Si recibimos nombres de jugadores, actualizarlos y guardarlos
						if (data.player1 && data.player2) {
							document.querySelector('#leftPlayerName').textContent = data.player1;
							document.querySelector('#rightPlayerName').textContent = data.player2;

							const existingData = getSavedGameData(gameId) || {};
							saveGameData(gameId, {
								...existingData,
								player1: data.player1,
								player2: data.player2
							});
						}
						// Si no tenemos nombres pero hay datos guardados, usarlos
						else {
							const savedData = getSavedGameData(gameId);
							if (savedData && savedData.player1 && savedData.player2) {
								document.querySelector('#leftPlayerName').textContent = savedData.player1;
								document.querySelector('#rightPlayerName').textContent = savedData.player2;
							}
						}
					}
					handleGameState(data.state);
					break;

				case 'game_finished':
					handleGameEnd(data);
					break;

				case 'player_disconnected':
					handleOpponentDisconnect(data);
					break;

				case 'player_reconnected':
					handleOpponentReconnect(data);
					break;
			}
		};

		return socket;
	}

	// Iniciar conexión inicial
	socket = setupConnection();

	// Función para manejar desconexión
	function handleDisconnection() {
		if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
			console.log('Máximo de intentos de reconexión alcanzado.');
			// Mostrar mensaje de error permanente
			showReconnectionFailed();
			return;
		}

		reconnecting = true;
		reconnectAttempts++;

		// Mostrar estado de reconexión
		document.getElementById('gameStatus').textContent =
			`🔄 Conexión perdida. Reintentando... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`;

		// Mostrar overlay de reconexión
		showReconnectionAttempt(reconnectAttempts, MAX_RECONNECT_ATTEMPTS);

		// Intentar reconectar después de intervalo
		setTimeout(() => {
			if (reconnecting) {
				setupConnection();
			}
		}, RECONNECT_INTERVAL);
	}

	// Función para mostrar intentos de reconexión
	function showReconnectionAttempt(attempt, max) {
		// Verificar si ya existe el overlay, sino crearlo
		let reconnectOverlay = document.getElementById('reconnectOverlay');
		if (!reconnectOverlay) {
			reconnectOverlay = document.createElement('div');
			reconnectOverlay.id = 'reconnectOverlay';
			reconnectOverlay.style.position = 'absolute';
			reconnectOverlay.style.inset = '0';
			reconnectOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
			reconnectOverlay.style.zIndex = '1000';
			reconnectOverlay.style.display = 'flex';
			reconnectOverlay.style.justifyContent = 'center';
			reconnectOverlay.style.alignItems = 'center';
			reconnectOverlay.style.flexDirection = 'column';
			reconnectOverlay.style.color = 'white';
			reconnectOverlay.style.fontSize = '1.5rem';

			const spinner = document.createElement('div');
			spinner.className = 'spinner-border text-light mb-3';
			spinner.setAttribute('role', 'status');

			const message = document.createElement('div');
			message.id = 'reconnectMessage';

			reconnectOverlay.appendChild(spinner);
			reconnectOverlay.appendChild(message);

			document.querySelector('.game-wrapper').appendChild(reconnectOverlay);
		}

		document.getElementById('reconnectMessage').textContent =
			`Reconectando... (${attempt}/${max})`;
	}

	// Función para mostrar reconexión exitosa
	function showReconnectionSuccess() {
		const reconnectOverlay = document.getElementById('reconnectOverlay');
		if (reconnectOverlay) {
			reconnectOverlay.style.backgroundColor = 'rgba(0, 128, 0, 0.7)';
			document.getElementById('reconnectMessage').textContent = '¡Reconectado con éxito!';

			// Remover el overlay después de 2 segundos
			setTimeout(() => {
				reconnectOverlay.remove();
			}, 2000);
		}
	}

	// Función para mostrar reconexión fallida
	function showReconnectionFailed() {
		const reconnectOverlay = document.getElementById('reconnectOverlay');
		if (reconnectOverlay) {
			reconnectOverlay.style.backgroundColor = 'rgba(128, 0, 0, 0.7)';
			document.getElementById('reconnectMessage').textContent =
				'No se pudo reconectar. La partida se ha perdido.';

			// Añadir botón para volver al lobby
			const backButton = document.createElement('button');
			backButton.className = 'btn btn-light mt-3';
			backButton.textContent = 'Volver al menú';
			backButton.onclick = () => window.location.href = '/game';
			reconnectOverlay.appendChild(backButton);
		}
	}

	// Función para manejar la desconexión de oponente
	function handleOpponentDisconnect(data) {
		const opponentSide = data.side;

		// Mostrar mensaje de desconexión
		const statusEl = document.createElement('div');
		statusEl.className = 'opponent-disconnect-status';
		statusEl.textContent = `Oponente desconectado (${opponentSide})`;
		statusEl.style.position = 'absolute';
		statusEl.style.bottom = '20px';
		statusEl.style.left = '20px';
		statusEl.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
		statusEl.style.color = 'white';
		statusEl.style.padding = '10px';
		statusEl.style.borderRadius = '5px';

		const wrapper = document.querySelector('.game-wrapper');
		wrapper.appendChild(statusEl);

		// Remover el mensaje después de 5 segundos
		setTimeout(() => {
			statusEl.remove();
		}, 5000);
	}

	// Función para manejar la reconexión de oponente
	function handleOpponentReconnect(data) {
		const opponentSide = data.side;
		const opponentName = data.username;

		// Mostrar mensaje de reconexión
		const statusEl = document.createElement('div');
		statusEl.className = 'opponent-reconnect-status';
		statusEl.textContent = `${opponentName} reconectado (${opponentSide})`;
		statusEl.style.position = 'absolute';
		statusEl.style.bottom = '20px';
		statusEl.style.left = '20px';
		statusEl.style.backgroundColor = 'rgba(0, 255, 0, 0.7)';
		statusEl.style.color = 'white';
		statusEl.style.padding = '10px';
		statusEl.style.borderRadius = '5px';

		const wrapper = document.querySelector('.game-wrapper');
		wrapper.appendChild(statusEl);

		// Remover el mensaje después de 5 segundos
		setTimeout(() => {
			statusEl.remove();
		}, 5000);
	}

	async function showPreMatchSequence(player1, player2, playerSide) {
		return new Promise(async (resolve) => {
			const modal = document.getElementById('matchFoundModal');
			const countdown = document.getElementById('countdown');

			// 1. Mostrar modal inicial
			document.getElementById('player1NamePreMatch').textContent = player1;
			document.getElementById('player2NamePreMatch').textContent = player2;
			document.getElementById('playerControls').textContent =
				playerSide === 'left' ? 'W / S' : '↑ / ↓';

			modal.style.display = 'flex';
			await new Promise(r => setTimeout(r, 2000));

			// 2. Ocultar modal
			modal.style.animation = 'fadeOut 0.5s ease-out';
			await new Promise(r => setTimeout(r, 500));
			modal.style.display = 'none';

			// 3. Mostrar cuenta regresiva
			countdown.style.display = 'flex';
			countdown.textContent = '';

			// 4. --->>> Decimos al servidor que estamos listos para la cuenta atrás
			socket.send(JSON.stringify({
				type: 'ready_for_countdown'
			}));

			resolve();
		});
	}

	let gameStarted = false; // Nueva variable de estado
	let countdownShown = false;

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
		const gameOverScreen = document.getElementById('gameOverScreen');
		const winnerText = document.getElementById('winnerText');
		const resultIcon = document.querySelector('.result-icon i');
		const player1Score = document.querySelector('.player1-score');
		const player2Score = document.querySelector('.player2-score');

		// Determinar jugadores según el lado
		const leftPlayerName = document.querySelector('#leftPlayerName').textContent;
		const rightPlayerName = document.querySelector('#rightPlayerName').textContent;

		// Actualizar nombres finales con los nombres correctos
		document.getElementById('finalPlayer1Name').textContent = leftPlayerName;
		document.getElementById('finalPlayer2Name').textContent = rightPlayerName;

		// Actualizar puntuaciones
		player1Score.textContent = data.final_score.left;
		player2Score.textContent = data.final_score.right;

		// Configurar estilo según victoria/derrota
		if (data.winner === playerSide) {
			gameOverScreen.classList.add('victory');
			gameOverScreen.classList.remove('defeat');
			winnerText.textContent = '¡Victoria!';
			resultIcon.className = 'fas fa-trophy';
		} else {
			gameOverScreen.classList.add('defeat');
			gameOverScreen.classList.remove('victory');
			winnerText.textContent = 'Derrota';
			resultIcon.className = 'fas fa-flag';
		}

		// Simplificar la configuración del botón de retorno
		document.getElementById('returnToLobby').onclick = () => {
			window.location.href = '/game';
		};

		gameOverScreen.style.display = 'flex';

		// Animaciones de números
		animateScore(player1Score, data.final_score.left);
		animateScore(player2Score, data.final_score.right);

		// Eliminar datos guardados cuando termina el juego
		localStorage.removeItem(`game_${gameId}`);
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

		// Si ya existe un intervalo, no crear uno nuevo
		if (movementInterval) {
			clearInterval(movementInterval);
		}

		// Iniciar el intervalo de movimiento continuo
		movementInterval = setInterval(() => {
			if (activeKeys.size > 0 && playerSide && socket?.readyState === WebSocket.OPEN) {
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
			movementInterval = null;
		}
		document.removeEventListener('keydown', handleKeyDown);
		document.removeEventListener('keyup', handleKeyUp);

		// Cierre controlado del socket
		if (socket && socket.readyState === WebSocket.OPEN) {
			socket.close(1000, 'Vista desmontada');
		}

		// Eliminar el CSS si no hay otras vistas que lo usen
		const cssLink = document.querySelector('link[href="/css/game.css"]');
		if (cssLink) {
			document.head.removeChild(cssLink);
		}

		document.removeEventListener('fullscreenchange', handleFullscreenChange);
		document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
		document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
		document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
	};

	// Funciones auxiliares para guardar y recuperar datos de juego
	function saveGameData(gameId, data) {
		try {
			localStorage.setItem(`game_${gameId}`, JSON.stringify(data));
			console.log('Datos de juego guardados:', data);
		} catch (e) {
			console.error('Error al guardar datos de juego:', e);
		}
	}

	function getSavedGameData(gameId) {
		try {
			const savedData = localStorage.getItem(`game_${gameId}`);
			return savedData ? JSON.parse(savedData) : null;
		} catch (e) {
			console.error('Error al recuperar datos de juego:', e);
			return null;
		}
	}
}
