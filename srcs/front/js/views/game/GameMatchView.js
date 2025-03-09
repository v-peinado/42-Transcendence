import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { gameReconnectionService } from '../../services/GameReconnectionService.js'; // Nueva importación

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
			document.getElementById('gameStatus').textContent = reconnecting ?
				'🔄 Reconectando a la partida...' : '🎮 Conectado - Esperando oponente...';

			// Si ya sabemos nuestro lado, configurar controles inmediatamente
			if (gameReconnectionService.getPlayerSide()) {
				playerSide = gameReconnectionService.getPlayerSide();
				setupControls();
			}
		},
		onMessage: (data) => {
			console.log('Mensaje recibido en GameMatchView:', data);

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
							console.log('Lado del jugador determinado desde game_info:', playerSide);
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
			}
		},
		onDisconnect: (attempt, max) => {
			document.getElementById('gameStatus').textContent =
				`🔄 Conexión perdida. Reintentando... (${attempt}/${max})`;
		},
		onReconnect: (data) => {
			document.getElementById('gameStatus').textContent = '🎮 Reconectado!';
		},
		onReconnectFailed: () => {
			document.getElementById('gameStatus').textContent = '❌ No se pudo reconectar';
		}
	});

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

			// 4. Decimos al servidor que estamos listos para la cuenta atrás
			gameReconnectionService.send({
				type: 'ready_for_countdown'
			});

			resolve();
		});
	}

	let gameStarted = false;
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

		// Si ya existe un intervalo, no crear uno nuevo
		if (movementInterval) {
			clearInterval(movementInterval);
		}

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
				gameReconnectionService.send(message);
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

		// Usar el servicio para desconectar WebSocket
		gameReconnectionService.disconnect();

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
}
