import { loadHTML } from '../../utils/htmlLoader.js';
import { soundService } from '../../services/SoundService.js';
import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { gameReconnectionService } from '../../services/GameReconnectionService.js';
import { diagnosticService } from '../../services/DiagnosticService.js';
import GameStateInterpolator from '../../utils/GameStateInterpolator.js';

export async function GameMatchView(gameId) {
	// Al principio de la función, registrar inicio
	diagnosticService.info('GameMatchView', `Starting game view for game ${gameId}`);

	console.log('Iniciando partida:', gameId);

	// Validar que tenemos un gameId válido
	if (!gameId || isNaN(parseInt(gameId))) {
		diagnosticService.error('GameMatchView', 'ID de partida inválido', { gameId });
		console.error('GameMatchView: ID de partida inválido');
		// Redirigir a Not Found en lugar de /game
		window.history.pushState(null, null, '/404');
		const NotFoundView = (await import('../NotFoundView.js')).NotFoundView;
		await NotFoundView();
		return;
	}

	// Asegurarnos que estamos autenticados
	const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
	if (!isAuthenticated) {
		diagnosticService.error('GameMatchView', 'Usuario no autenticado');
		console.error('GameMatchView: Usuario no autenticado');
		window.location.href = '/login?redirect=/game/' + gameId;
		return;
	}

	// Verificar si la partida existe y el usuario tiene acceso
	try {
		diagnosticService.info('GameMatchView', 'Verificando acceso a partida', { gameId });
		const gameAccess = await GameService.verifyGameAccess(gameId);

		if (!gameAccess.exists || !gameAccess.can_access) {
			diagnosticService.warn('GameMatchView', 'Acceso a partida denegado', gameAccess);
			console.error('GameMatchView: Acceso a partida denegado:', gameAccess.message);
			window.history.pushState(null, null, '/404');
			const NotFoundView = (await import('../NotFoundView.js')).NotFoundView;
			await NotFoundView();
			return;
		}
	} catch (error) {
		diagnosticService.error('GameMatchView', 'Error verificando acceso a partida', error);
		console.error('Error verificando acceso a partida:', error);
	}

	const app = document.getElementById('app');

	try {
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

		// Añadir botón de diagnóstico independientemente del gameControls
		const diagnosticBtn = document.createElement('button');
		diagnosticBtn.id = 'diagnosticBtn';
		diagnosticBtn.className = 'btn btn-sm btn-outline-info position-fixed';
		diagnosticBtn.title = 'Mostrar panel de diagnóstico';
		diagnosticBtn.innerHTML = '<i class="fas fa-stethoscope"></i>';
		diagnosticBtn.style.position = 'fixed';
		diagnosticBtn.style.bottom = '10px';
		diagnosticBtn.style.right = '10px';
		diagnosticBtn.style.zIndex = '900';
		diagnosticBtn.addEventListener('click', () => {
			diagnosticService.showDiagnosticPanel();
		});

		// Añadir al gameControls si existe, o directamente al documento si no
		const gameControls = document.querySelector('.game-controls');
		if (gameControls) {
			gameControls.appendChild(diagnosticBtn);
		} else {
			document.body.appendChild(diagnosticBtn);
			diagnosticService.warn('GameMatchView', 'gameControls no encontrado, botón añadido al body');
		}

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
				console.log(`[DEBUG] Conexión WebSocket abierta. Reconectando: ${reconnecting}`);
				const gameStatus = document.getElementById('gameStatus');
				if (gameStatus) { // Verificar que el elemento existe
					gameStatus.textContent = reconnecting ?
						'🔄 Reconectando a la partida...' : '🎮 Conectado - Esperando oponente...';
				}

				// Si ya sabemos nuestro lado, configurar controles inmediatamente
				if (gameReconnectionService.getPlayerSide()) {
					playerSide = gameReconnectionService.getPlayerSide();
					console.log(`[DEBUG] Lado recuperado del servicio: ${playerSide}`);
					setupControls();
				}
			},
			onMessage: (data) => {
				console.log(`[DEBUG] Mensaje recibido: ${data.type}`);

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
						// Si se trata de reconexión, hacer un manejo especial
						if (data.is_reconnection) {
							console.log('[DEBUG] Iniciando proceso de reconexión completa');

							// Inmediatamente guardar datos críticos en variables locales
							// antes de cualquier procesamiento asíncrono
							const reconnectionState = JSON.parse(JSON.stringify(data.state || {}));
							const reconnectionPlayerSide = data.player_side || playerSide;
							const reconnectionPlayer1 = data.player1;
							const reconnectionPlayer2 = data.player2;

							// Si es una sincronización específica para reconexión
							if (reconnectionState.reconnection_sync) {
								diagnosticService.info('GameMatchView', 'Estado de sincronización de reconexión recibido', {
									isSecondSync: reconnectionState.is_second_sync || false,
									timestamp: reconnectionState.server_timestamp
								});
							}

							// No más referencia externa a handleReconnection
							// Toda la lógica implementada directamente aquí
							(async () => {
								try {
									// 1. Detener todo procesamiento actual solo si no es una actualización de sincronización
									if (!reconnectionState.reconnection_sync) {
										console.log('[DEBUG] Reconexión - Limpiando estado actual');
										await cleanupGameState();
									}

									// 2. Actualizar información de jugador usando datos guardados
									if (reconnectionPlayerSide) {
										playerSide = reconnectionPlayerSide;
										console.log(`[DEBUG] Reconexión - Lado del jugador actualizado: ${playerSide}`);
									} else {
										console.log('[DEBUG] Reconexión - No se recibió lado del jugador');
									}

									// 3. Actualizar estado del juego con los datos guardados
									console.log('[DEBUG] Reconexión - Actualizando estado del juego');

									// Si es un estado de sincronización específico para reconexión,
									// procesar de manera especial para garantizar transiciones suaves
									if (reconnectionState.reconnection_sync) {
										// Aquí simplemente pasamos el estado para que handleGameState
										// se encargue de la interpolación
										handleGameState(reconnectionState);
									} else {
										gameState = reconnectionState;
										console.log(`[DEBUG] Estado del juego actualizado:`, gameState);
										drawGame();
									}

									// 4. Actualizar UI con nombres de jugadores guardados
									if (reconnectionPlayer1) {
										const leftNameEl = document.querySelector('#leftPlayerName');
										if (leftNameEl) {
											leftNameEl.textContent = reconnectionPlayer1;
											console.log(`[DEBUG] Reconexión - Nombre del jugador 1 actualizado: ${reconnectionPlayer1}`);
										} else {
											console.error('[DEBUG] Reconexión - No se encontró el elemento #leftPlayerName');
										}
									}

									if (reconnectionPlayer2) {
										const rightNameEl = document.querySelector('#rightPlayerName');
										if (rightNameEl) {
											rightNameEl.textContent = reconnectionPlayer2;
											console.log(`[DEBUG] Reconexión - Nombre del jugador 2 actualizado: ${reconnectionPlayer2}`);
										} else {
											console.error('[DEBUG] Reconexión - No se encontró el elemento #rightPlayerName');
										}
									}

									// Resto del código igual...
									// 5. Restaurar elementos UI que pudieran haberse perdido
									console.log('[DEBUG] Reconexión - Restaurando UI');

									// Restaurar UI directamente aquí (en lugar de llamar a restoreGameUI)
									try {
										// Restaurar el botón de chat si se ha perdido
										const chatContainer = document.querySelector('.game-chat-container');
										const chatButton = document.querySelector('.chat-toggle-btn');
										const gameControls = document.querySelector('.game-controls');

										console.log('[DEBUG] Reconexión - Estado actual:', {
											chatContainerExists: !!chatContainer,
											chatButtonExists: !!chatButton,
											gameControlsExists: !!gameControls
										});

										if (!chatButton && chatContainer && gameControls) {
											console.log('[DEBUG] Reconexión - Recreando botón de chat');
											const newChatButton = document.createElement('button');
											newChatButton.className = 'chat-toggle-btn';
											newChatButton.innerHTML = '<i class="fas fa-comments"></i>';
											newChatButton.addEventListener('click', () => {
												chatContainer.classList.toggle('chat-open');
												newChatButton.classList.toggle('active');
											});
											gameControls.appendChild(newChatButton);
											console.log('[DEBUG] Reconexión - Botón de chat recreado');
										}

										// Asegurar que el chat está en estado cerrado tras reconexión
										if (chatContainer) {
											chatContainer.classList.remove('chat-open');
											if (chatButton) chatButton.classList.remove('active');
											console.log('[DEBUG] Reconexión - Chat cerrado correctamente');
										}
									} catch (error) {
										console.error('[DEBUG] Error al restaurar UI:', error);
									}

									// 6. Redibujar el canvas con el nuevo estado
									if (gameState) {
										console.log('[DEBUG] Reconexión - Redibujando canvas');
										drawGame();
									} else {
										console.error('[DEBUG] Reconexión - No se puede redibujar, gameState es null');
									}

									// 7. Configurar controles con retardo para asegurar sincronización
									console.log('[DEBUG] Reconexión - Configurando controles con retardo');
									setTimeout(() => {
										setupControls();
										const gameStatusEl = document.getElementById('gameStatus');
										if (gameStatusEl) {
											gameStatusEl.textContent = '🎮 Reconectado - Partida en curso';
										}
										console.log('[DEBUG] Reconexión - Proceso completado');
									}, 800);
								} catch (error) {
									console.error('[DEBUG] Error en proceso de reconexión:', error);
								}
							})();
						} else {
							handleGameState(data.state);
						}
						break;

					case 'game_finished':
						handleGameEnd(data);
						break;

					case 'fast_state':
						// Nuevo: Manejo de reconexión rápida
						diagnosticService.info('GameMatchView', 'Estado rápido recibido para reconexión', {
							timestamp: data.timestamp
						});

						// Mostrar mensaje de reconexión exitosa
						const gameStatus = document.getElementById('gameStatus');
						if (gameStatus) {
							gameStatus.textContent = '🎮 Reconexión rápida completada';
							gameStatus.style.color = '#4caf50';
							setTimeout(() => {
								gameStatus.style.color = '';
								gameStatus.textContent = '🎮 Conectado';
							}, 1000);
						}

						// Construimos un gameState compatible con nuestro handler
						const fastGameState = {
							ball: data.ball,
							paddles: data.paddles,
							status: data.status,
							reconnection_sync: true,
							fast_reconnect: true,
							server_timestamp: data.timestamp
						};

						// Actualizar puntuaciones si están disponibles
						if (data.score) {
							if (fastGameState.paddles && fastGameState.paddles.left) {
								fastGameState.paddles.left.score = data.score.left;
							}
							if (fastGameState.paddles && fastGameState.paddles.right) {
								fastGameState.paddles.right.score = data.score.right;
							}
						}

						// Establecer playerSide si viene en la respuesta
						if (data.player_side && !playerSide) {
							playerSide = data.player_side;
							setupControls(); // Configurar controles inmediatamente
						}

						// Aplicar el estado y mostrar animación de reconexión exitosa
						handleGameState(fastGameState);
						canvas.classList.add('reconnected');
						setTimeout(() => canvas.classList.remove('reconnected'), 300);
						break;

					case 'game_prediction':
						// Nuevo: Datos de predicción para movimientos más suaves
						handlePredictionData(data);
						break;
				}
			},
			onDisconnect: (attempt, max) => {
				document.getElementById('gameStatus').textContent =
					`🔄 Conexión perdida. Reintentando... (${attempt}/${max})`;
			},
			onReconnect: (data) => {
				const gameStatus = document.getElementById('gameStatus');
				if (gameStatus) { // Verificar que el elemento existe
					gameStatus.textContent = '🎮 Reconectado!';
				}
			},
			onFastReconnect: (data) => {
				// Actualizamos la interfaz para reconexión rápida
				const gameStatus = document.getElementById('gameStatus');
				if (gameStatus) {
					gameStatus.textContent = '⚡ Reconexión ultra-rápida';
					gameStatus.style.color = '#4caf50';
					setTimeout(() => {
						gameStatus.style.color = '';
						gameStatus.textContent = '🎮 Conectado';
					}, 1000);
				}

				// Configurar controles inmediatamente
				if (data.player_side) {
					playerSide = data.player_side;
					setupControls();
				}

				// Mostrar animación de reconexión exitosa
				canvas.classList.add('reconnected');
				setTimeout(() => canvas.classList.remove('reconnected'), 300);
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

			// Guardar estado anterior para posible interpolación en reconexiones
			const previousState = gameState;

			// Actualizar el estado actual
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

			// OPTIMIZACIÓN: Manejar mejor la interpolación para reconexiones
			if (state.reconnection_sync && state.ball) {
				diagnosticService.debug('GameMatchView', 'Recibido estado de sincronización para reconexión', {
					serverTimestamp: state.server_timestamp,
					isSecondSync: state.is_second_sync || false
				});

				// Solo interpolamos si no es el primer estado de sincronización
				if (previousState && previousState.reconnection_sync && !previousState.is_second_sync && state.is_second_sync) {
					// Aquí tenemos dos estados de sincronización seguidos, podemos hacer una transición suave
					diagnosticService.debug('GameMatchView', 'Aplicando interpolación suave para la reconexión');

					// Animar reconexión en el canvas
					canvas.classList.add('reconnected');
					setTimeout(() => canvas.classList.remove('reconnected'), 500);

					// OPTIMIZACIÓN: Crear una secuencia más fluida de estados intermedios
					const steps = 3; // Crear 3 estados intermedios
					const sequence = GameStateInterpolator.createTransitionSequence(previousState, state, steps);

					// Dibujar la secuencia con un intervalo corto entre frames
					sequence.forEach((intermediateState, index) => {
						setTimeout(() => {
							gameState = intermediateState;
							drawGame(true); // Parámetro true indica estado de transición
						}, index * 10); // 10ms entre cada frame para una animación más fluida
					});

					return; // Terminamos aquí para que no se dibuje de inmediato
				}
			}

			// Si es fast-reconnect, animar inmediatamente
			if (state.fast_reconnect) {
				canvas.classList.add('reconnected');
				setTimeout(() => canvas.classList.remove('reconnected'), 300);
			}

			// Dibujar el estado del juego normalmente si no es un caso especial
			drawGame();
		}

		// Optimizar la función drawGame para suavizar movimientos en reconexión
		function drawGame(isTransition = false) {
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

			// Dibujar pelota con posible interpolación en reconexión
			if (gameState.ball) {
				if (gameState.reconnection_sync && gameState.ball.speed_x && gameState.ball.speed_y) {
					// OPTIMIZACIÓN: Mejorar la predicción basada en velocidad
					const now = Date.now();
					const serverTimestamp = gameState.server_timestamp || now;
					const timeDiff = Math.min(100, now - serverTimestamp); // Máximo 100ms de predicción

					// Simular el movimiento de la pelota según su velocidad y el tiempo transcurrido
					const predictedX = gameState.ball.x + (gameState.ball.speed_x * timeDiff / 16);
					const predictedY = gameState.ball.y + (gameState.ball.speed_y * timeDiff / 16);

					// Dibujar en la posición predicha
					ctx.beginPath();
					ctx.arc(predictedX, predictedY, gameState.ball.radius || 5, 0, Math.PI * 2);
					ctx.fill();

					// Durante transiciones, mostrar estela para hacer más suave el movimiento
					if (isTransition) {
						// Estela con transparencia para un efecto de movimiento suave
						ctx.globalAlpha = 0.3;
						ctx.beginPath();
						ctx.arc(gameState.ball.x, gameState.ball.y, gameState.ball.radius || 5, 0, Math.PI * 2);
						ctx.fill();
						ctx.globalAlpha = 1.0;
					}
				} else {
					// Dibujo normal sin predicción
					ctx.beginPath();
					ctx.arc(gameState.ball.x, gameState.ball.y, gameState.ball.radius || 5, 0, Math.PI * 2);
					ctx.fill();
				}
			}
		}

		// Nuevo método para manejar datos de predicción
		function handlePredictionData(data) {
			if (!gameState || !data) return;

			diagnosticService.debug('GameMatchView', 'Aplicando datos de predicción', {
				timestamp: data.timestamp
			});

			// Calcular el tiempo transcurrido desde que se enviaron los datos
			const now = Date.now();
			const predictionTime = now - (data.timestamp || now);

			// Aplicar predicción a la pelota si existe
			if (gameState.ball && data.ball) {
				// Guardar posiciones anteriores
				gameState.ball.prev_x = gameState.ball.x;
				gameState.ball.prev_y = gameState.ball.y;

				// Actualizar velocidades
				gameState.ball.speed_x = data.ball.speed_x;
				gameState.ball.speed_y = data.ball.speed_y;

				// Predecir posición actual basada en el tiempo transcurrido
				if (predictionTime > 0) {
					const predictionFactor = predictionTime / 1000; // Convertir a segundos
					gameState.ball.x = data.ball.x + (data.ball.speed_x * predictionFactor);
					gameState.ball.y = data.ball.y + (data.ball.speed_y * predictionFactor);
				} else {
					gameState.ball.x = data.ball.x;
					gameState.ball.y = data.ball.y;
				}
			}

			// Actualizar datos de palas
			if (gameState.paddles && data.paddles) {
				if (gameState.paddles.left && data.paddles.left) {
					gameState.paddles.left.y = data.paddles.left.y;
					gameState.paddles.left.moving = data.paddles.left.moving || false;
					gameState.paddles.left.direction = data.paddles.left.direction || 0;
				}
				if (gameState.paddles.right && data.paddles.right) {
					gameState.paddles.right.y = data.paddles.right.y;
					gameState.paddles.right.moving = data.paddles.right.moving || false;
					gameState.paddles.right.direction = data.paddles.right.direction || 0;
				}
			}

			// Redibujar el juego con la nueva predicción
			drawGame();
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
			// No procesar si el foco está en un input (para que el chat u otros campos funcionen)
			if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
				console.log('[DEBUG] handleKeyDown - Ignorando evento en input/textarea');
				return;
			}

			// No procesar si no tenemos un lado asignado
			if (!playerSide) {
				console.log('[DEBUG] handleKeyDown - Ignorando evento sin lado asignado');
				return;
			}

			// Solo procesar si el juego está en estado "playing"
			if (!gameState || gameState.status !== 'playing') {
				console.log(`[DEBUG] handleKeyDown - Ignorando evento, estado: ${gameState?.status || 'sin estado'}`);
				return;
			}

			// Verificar si la pala está lista para recibir comandos
			const paddle = gameState.paddles[playerSide];
			if (paddle && paddle.ready_for_input === false) {
				console.log('[DEBUG] handleKeyDown - Ignorando evento, pala no lista para comandos');
				return;
			}

			const key = e.key.toLowerCase();
			const isValidKey = (playerSide === 'left' && (key === 'w' || key === 's')) ||
				(playerSide === 'right' && (key === 'arrowup' || key === 'arrowdown'));

			if (!isValidKey) {
				console.log(`[DEBUG] handleKeyDown - Tecla no válida: ${key} para lado ${playerSide}`);
				return;
			}

			console.log(`[DEBUG] handleKeyDown - Procesando tecla: ${key} para lado ${playerSide}`);
			e.preventDefault();
			activeKeys.add(key);
			console.log(`[DEBUG] handleKeyDown - Teclas activas: ${[...activeKeys].join(', ')}`);

			diagnosticService.trace('GameMatchView', `Key down: ${key}`, {
				playerSide,
				gameState: gameState?.status,
				activeKeys: [...activeKeys]
			});
		}

		function handleKeyUp(e) {
			const key = e.key.toLowerCase();
			console.log(`[DEBUG] handleKeyUp - Tecla liberada: ${key}`);

			// Siempre eliminar la tecla del conjunto independientemente de otras condiciones
			if (activeKeys.has(key)) {
				activeKeys.delete(key);
				console.log(`[DEBUG] handleKeyUp - Tecla eliminada, teclas restantes: ${[...activeKeys].join(', ')}`);
			}

			// No procesar más si no tenemos un lado asignado
			if (!playerSide) {
				console.log('[DEBUG] handleKeyUp - No hay lado asignado, no se envía comando');
				return;
			}

			// Determinar si es una tecla de movimiento para este jugador
			const isMovementKey = (playerSide === 'left' && (key === 'w' || key === 's')) ||
				(playerSide === 'right' && (key === 'arrowup' || key === 'arrowdown'));

			// Si se soltó una tecla de movimiento o no quedan teclas activas, enviar comando
			if (isMovementKey || activeKeys.size === 0) {
				// Verificar direcciones restantes
				const remainingDirection = getDirection();
				console.log(`[DEBUG] handleKeyUp - Dirección restante: ${remainingDirection}`);

				// Siempre enviar comando cuando se suelta una tecla de movimiento
				if (isMovementKey) {
					console.log(`[DEBUG] handleKeyUp - Enviando comando de movimiento: ${remainingDirection}`);
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

			diagnosticService.trace('GameMatchView', `Key up: ${key}`, {
				playerSide,
				remaining: [...activeKeys]
			});
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

		// Optimizar la limpieza de estado
		async function cleanupGameState() {
			console.log('[DEBUG] cleanupGameState - Limpiando estado del juego');

			return new Promise(resolve => {
				try {
					// OPTIMIZACIÓN: Envío de comandos de parada más eficiente
					if (playerSide) {
						console.log(`[DEBUG] cleanupGameState - Enviando comando de parada para lado: ${playerSide}`);
						const userId = localStorage.getItem('user_id');
						gameReconnectionService.send({
							type: 'move_paddle',
							direction: 0,
							side: playerSide,
							player_id: parseInt(userId),
							force_stop: true,
							critical: true, // Marcar como crítico para priorización
							timestamp: Date.now(),
							message_id: `cleanup_stop_${Date.now()}`
						});
					}

					// 1. Detener cualquier animación o intervalo en curso
					if (movementInterval) {
						clearInterval(movementInterval);
						movementInterval = null;
					}

					// 2. Eliminar todos los listeners de eventos
					document.removeEventListener('keydown', handleKeyDown);
					document.removeEventListener('keyup', handleKeyUp);

					// 3. Reiniciar conjunto de teclas activas
					activeKeys = new Set();

					// 4. Esperar un breve periodo optimizado
					setTimeout(() => {
						resolve();
					}, 50); // Reducido a 50ms

				} catch (error) {
					console.error('[DEBUG] Error en cleanupGameState:', error);
					resolve(); // Resolver de todas formas para no bloquear
				}
			});
		}

		function setupControls() {
			diagnosticService.debug('GameMatchView', `Setting up controls for side: ${playerSide || 'not assigned'}`);

			try {
				// Limpieza forzada primero para evitar controles duplicados
				if (movementInterval) {
					clearInterval(movementInterval);
					movementInterval = null;
					console.log('[DEBUG] setupControls - Intervalo de movimiento previo eliminado');
				}

				document.removeEventListener('keydown', handleKeyDown);
				document.removeEventListener('keyup', handleKeyUp);
				console.log('[DEBUG] setupControls - Event listeners previos eliminados');

				// Reinicializar activeKeys
				activeKeys = new Set();
				console.log('[DEBUG] setupControls - Conjunto de teclas activas reinicializado');

				// Verificar que tenemos lo necesario para configurar controles
				if (!playerSide) {
					console.error('[DEBUG] setupControls - No hay lado de jugador asignado, no se pueden configurar controles');
					return;
				}

				// Agregar event listeners con referencias estables
				document.addEventListener('keydown', handleKeyDown);
				document.addEventListener('keyup', handleKeyUp);
				console.log('[DEBUG] setupControls - Nuevos event listeners agregados');

				// Iniciar intervalo para movimiento continuo
				movementInterval = setInterval(() => {
					// Solo enviar si hay teclas activas y juego en estado "playing"
					if (activeKeys.size > 0 && gameState?.status === 'playing') {
						const direction = getDirection();
						if (direction !== 0) {  // Solo enviar si hay dirección
							const message = {
								type: 'move_paddle',
								direction: direction,
								side: playerSide,
								player_id: parseInt(userId),
								timestamp: Date.now()
							};
							gameReconnectionService.send(message);
						}
					}
				}, 16);  // ~60 FPS

				console.log('[DEBUG] setupControls - Intervalo de movimiento configurado');
				console.log('[DEBUG] setupControls - Configuración completada');

			} catch (error) {
				diagnosticService.error('GameMatchView', 'Error in setupControls', error);
			}
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
			diagnosticService.info('GameMatchView', 'Cleaning up game view');
			cleanupGameState();

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
	} catch (error) {
		diagnosticService.error('GameMatchView', 'Error loading game view', error);
		console.error('Error al cargar la vista del juego:', error);
		// Mostrar NotFoundView en caso de error
		const NotFoundView = (await import('../NotFoundView.js')).NotFoundView;
		await NotFoundView();
	}
}
