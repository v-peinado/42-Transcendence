import { diagnosticService } from './DiagnosticService.js';

class GameReconnectionService {
	constructor() {
		this.socket = null;
		this.gameId = null;
		this.playerSide = null;
		this.reconnecting = false;
		this.reconnectAttempts = 0;
		this.MAX_RECONNECT_ATTEMPTS = 15;
		this.RECONNECT_INTERVAL = 2000;
		this.connectionId = null;
		this.heartbeatInterval = null;
		this.lastMessageTime = Date.now();
		this.healthCheckEvents = [];
	}

	// Configura la conexión WebSocket y maneja reconexiones
	setupConnection(gameId, callbacks = {}) {
		this.gameId = gameId;
		this.callbacks = callbacks;
		this.connectionId = `game_${gameId}_${Date.now()}`;

		diagnosticService.debug('GameReconnection', `Setting up connection for game ${gameId}`, {
			reconnecting: this.reconnecting,
			attempts: this.reconnectAttempts
		});

		const userId = localStorage.getItem('user_id');

		// Usar el nuevo método de recuperación de datos 
		this.recoverReconnectionData(gameId);

		// Crear conexión WebSocket
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws/game/${gameId}/`;

		diagnosticService.connectionEvent('attempt', {
			url: wsUrl,
			reconnecting: this.reconnecting,
			gameId,
			connectionId: this.connectionId
		});

		// Cerrar socket existente si hubiera
		if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
			diagnosticService.debug('GameReconnection', 'Closing existing socket', {
				readyState: this.socket.readyState
			});
			try {
				this.socket.close(1000, 'Creando nueva conexión');
			} catch (e) {
				diagnosticService.error('GameReconnection', 'Error closing socket', e);
			}
		}

		try {
			this.socket = new WebSocket(wsUrl);

			// Registrar el socket para diagnóstico
			diagnosticService.trackWebSocket(this.socket, this.connectionId);

			// Limpiar cualquier heartbeat anterior
			if (this.heartbeatInterval) {
				clearInterval(this.heartbeatInterval);
				this.heartbeatInterval = null;
			}

			this.socket.onopen = (event) => {
				diagnosticService.info('GameReconnection', 'WebSocket connection established', {
					reconnecting: this.reconnecting,
					readyState: this.socket.readyState,
					connectionId: this.connectionId
				});

				this.lastMessageTime = Date.now();

				if (this.callbacks.onOpen) {
					this.callbacks.onOpen(this.reconnecting);
				}

				// Si estamos reconectando, implementar protocolo FAST RECONNECT inmediato
				if (this.reconnecting && this.playerSide) {
					diagnosticService.info('GameReconnection', 'Initiating fast reconnect protocol');

					// Enviar inmediatamente la petición con todos los datos necesarios
					this.send({
						type: 'fast_reconnect',
						player_id: parseInt(userId),
						game_id: parseInt(gameId),
						side: this.playerSide,
						connectionId: this.connectionId,
						timestamp: Date.now(),
						critical: true // Marcar como crítico para priorización
					});

					diagnosticService.debug('GameReconnection', 'Fast reconnect request sent');

					// Como respaldo, también enviar la solicitud tradicional después de un breve retraso
					setTimeout(() => {
						if (this.socket && this.socket.readyState === WebSocket.OPEN) {
							this.send({
								type: 'request_game_state',
								player_id: parseInt(userId),
								game_id: parseInt(gameId),
								connectionId: this.connectionId,
								timestamp: Date.now()
							});
							diagnosticService.debug('GameReconnection', 'Backup state request sent');
						}
					}, 200);
				}

				// Configurar health check
				this.startHealthCheck();
			};

			this.socket.onmessage = (event) => {
				// Actualizar timestamp de último mensaje
				this.lastMessageTime = Date.now();

				// Procesar el mensaje
				try {
					const data = JSON.parse(event.data);

					// Registrar todos los mensajes para diagnóstico (excepto actualizaciones de estado del juego que son muy frecuentes)
					if (data.type !== 'game_state') {
						diagnosticService.debug('GameReconnection', `Message received: ${data.type}`, {
							messageType: data.type,
							isReconnection: data.is_reconnection
						});
					}

					// NUEVO: Manejar protocolo fast reconnect
					if (data.type === 'fast_state') {
						this.handleFastReconnect(data);
					}
					// Para reconexión tradicional
					else if (data.type === 'game_state' && (data.is_reconnection || this.reconnecting)) {
						this.handleReconnectionSuccess(data);
					} else if (data.type === 'game_prediction') {
						this.handlePredictionData(data);
					} else if (data.type === 'player_disconnected') {
						this.handleOpponentDisconnect(data);
					} else if (data.type === 'player_reconnected') {
						this.handleOpponentReconnect(data);
					}

					// Pasar el mensaje al callback
					if (this.callbacks.onMessage) {
						this.callbacks.onMessage(data);
					}
				} catch (error) {
					diagnosticService.error('GameReconnection', 'Error processing message', {
						error,
						rawData: event.data.substring(0, 200) // solo primeros 200 caracteres para evitar logs enormes
					});
				}
			};

			this.socket.onclose = (event) => {
				diagnosticService.info('GameReconnection', 'Connection closed', {
					code: event.code,
					reason: event.reason,
					wasClean: event.wasClean
				});

				// Detener health check
				if (this.heartbeatInterval) {
					clearInterval(this.heartbeatInterval);
					this.heartbeatInterval = null;
				}

				// Solo intentar reconectar si no fue un cierre controlado
				if (event.code !== 1000 && !document.getElementById('gameOverScreen')?.style?.display === 'flex') {
					this.handleDisconnection();
				}
			};

			this.socket.onerror = (error) => {
				diagnosticService.error('GameReconnection', 'WebSocket error', {
					error: error.message || 'Unknown error'
				});
				this.handleDisconnection();
			};
		} catch (error) {
			diagnosticService.error('GameReconnection', 'Error creating WebSocket', error);
			this.handleDisconnection();
		}

		return this.socket;
	}

	// Iniciar verificaciones de salud de la conexión
	startHealthCheck() {
		if (this.heartbeatInterval) {
			clearInterval(this.heartbeatInterval);
		}

		this.healthCheckEvents = [];

		// Hacer health check cada 5 segundos
		this.heartbeatInterval = setInterval(() => {
			const now = Date.now();
			const elapsedSinceLastMessage = now - this.lastMessageTime;

			// Si han pasado más de 15 segundos sin mensajes, la conexión podría estar muerta
			if (elapsedSinceLastMessage > 15000) {
				const event = {
					time: now,
					type: 'connection_stale',
					elapsed: elapsedSinceLastMessage
				};
				this.healthCheckEvents.push(event);

				diagnosticService.warn('GameReconnection', 'Connection stale, no messages received', {
					elapsedMs: elapsedSinceLastMessage,
					socketState: this.socket?.readyState
				});

				// Si han pasado más de 30 segundos, consideramos la conexión muerta y forzamos reconexión
				if (elapsedSinceLastMessage > 30000) {
					diagnosticService.error('GameReconnection', 'Connection dead, forcing reconnection');

					// Forzar cierre y reconexión
					try {
						if (this.socket) {
							this.socket.close(3000, 'Forcing reconnection due to inactivity');
						}
					} catch (e) {
						diagnosticService.error('GameReconnection', 'Error forcing socket close', e);
					}

					// Iniciar proceso de reconexión manualmente
					this.handleDisconnection();
					return;
				}
			}

			// Enviar ping para verificar conexión
			if (this.socket?.readyState === WebSocket.OPEN) {
				try {
					const pingData = {
						type: 'ping',
						timestamp: now,
						connectionId: this.connectionId,
						side: this.playerSide,
						userId: localStorage.getItem('user_id')
					};

					this.send(pingData);

					// Guardar evento de ping para diagnosticar latencia
					const pingTime = Date.now();

					// Crear un handler único para este ping específico
					const pongHandler = (event) => {
						try {
							const data = JSON.parse(event.data);
							if (data.type === 'pong' && data.client_timestamp === pingData.timestamp) {
								// Calcular latencia
								const latency = Date.now() - pingTime;

								const event = {
									time: Date.now(),
									type: 'pong_received',
									latency,
									serverTime: data.server_timestamp
								};

								// Guardar dato de latencia
								this.healthCheckEvents.push(event);

								// Si la latencia es demasiado alta, registrar advertencia
								if (latency > 1000) {
									diagnosticService.warn('GameReconnection', `Alta latencia detectada: ${latency}ms`);
								} else {
									diagnosticService.trace('GameReconnection', `Latencia: ${latency}ms`);
								}

								// Eliminar este handler después de procesarlo
								this.socket.removeEventListener('message', pongHandler);
							}
						} catch (e) {
							// Ignorar errores en el handler de pong
						}
					};

					// Añadir handler temporal para este ping
					if (this.socket) {
						this.socket.addEventListener('message', pongHandler);

						// Limpiar handler después de 10 segundos por si no hay respuesta
						setTimeout(() => {
							if (this.socket) {
								this.socket.removeEventListener('message', pongHandler);
							}
						}, 10000);
					}

					const event = {
						time: now,
						type: 'ping_sent',
						socketState: this.socket.readyState
					};
					this.healthCheckEvents.push(event);

					diagnosticService.trace('GameReconnection', 'Health check ping sent');
				} catch (e) {
					diagnosticService.error('GameReconnection', 'Error sending ping', e);
				}
			} else {
				const event = {
					time: now,
					type: 'socket_not_open',
					socketState: this.socket?.readyState
				};
				this.healthCheckEvents.push(event);

				diagnosticService.warn('GameReconnection', 'Cannot send ping, socket not open', {
					socketState: this.socket?.readyState
				});
			}

			// Limitar el tamaño del historial
			if (this.healthCheckEvents.length > 50) {
				this.healthCheckEvents = this.healthCheckEvents.slice(-50);
			}

		}, 5000);

		diagnosticService.debug('GameReconnection', 'Health check started');
	}

	// Maneja la desconexión e intenta reconectar
	handleDisconnection() {
		diagnosticService.info('GameReconnection', 'Handling disconnection', {
			attempts: this.reconnectAttempts,
			max: this.MAX_RECONNECT_ATTEMPTS
		});

		if (this.reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
			diagnosticService.warn('GameReconnection', 'Maximum reconnection attempts reached');
			this.showReconnectionFailed();
			if (this.callbacks.onReconnectFailed) {
				this.callbacks.onReconnectFailed();
			}
			return;
		}

		this.reconnecting = true;
		this.reconnectAttempts++;

		diagnosticService.connectionEvent('disconnect', {
			gameId: this.gameId,
			connectionId: this.connectionId,
			attempt: this.reconnectAttempts
		});

		if (this.callbacks.onDisconnect) {
			this.callbacks.onDisconnect(this.reconnectAttempts, this.MAX_RECONNECT_ATTEMPTS);
		}

		// Mostrar estado de reconexión
		this.showReconnectionAttempt(this.reconnectAttempts, this.MAX_RECONNECT_ATTEMPTS);

		// Intentar reconectar después de intervalo
		setTimeout(() => {
			if (this.reconnecting) {
				diagnosticService.info('GameReconnection', 'Attempting to reconnect', {
					attempt: this.reconnectAttempts,
					gameId: this.gameId
				});

				// Crear nueva ID de conexión para este intento
				this.connectionId = `game_${this.gameId}_${Date.now()}_attempt${this.reconnectAttempts}`;
				this.setupConnection(this.gameId, this.callbacks);
			}
		}, this.RECONNECT_INTERVAL);
	}

	// Optimizar el manejo de reconexión
	handleReconnectionSuccess(data) {
		diagnosticService.info('GameReconnection', 'Reconnection successful', {
			playerSide: data.player_side || this.playerSide,
			dataReceived: !!data
		});

		this.reconnecting = false;
		this.reconnectAttempts = 0;

		diagnosticService.connectionEvent('reconnect', {
			gameId: this.gameId,
			connectionId: this.connectionId
		});

		// OPTIMIZACIÓN: Eliminar la pausa
		// Si el servidor nos envía información del lado del jugador, usarla
		if (data.player_side) {
			this.playerSide = data.player_side;
			diagnosticService.debug('GameReconnection', `Player side received from server: ${this.playerSide}`);
		}

		// OPTIMIZACIÓN: Un solo comando de parada forzada
		if (this.playerSide && this.socket && this.socket.readyState === WebSocket.OPEN) {
			const userId = localStorage.getItem('user_id');
			const stopCommand = {
				type: 'move_paddle',
				direction: 0,
				side: this.playerSide,
				player_id: parseInt(userId),
				timestamp: Date.now(),
				force_stop: true,
				critical: true,
				message_id: `reconnect_stop_${Date.now()}`
			};

			diagnosticService.info('GameReconnection', 'Enviando comando de parada forzada tras reconexión');
			this.send(stopCommand);
		}

		// Guardar o actualizar datos
		const existingData = this.getSavedGameData(this.gameId) || {};

		let dataToSave = {
			...existingData,
			playerSide: this.playerSide,
			lastReconnection: Date.now()
		};

		// Si recibimos nombres de jugadores, guardarlos también
		if (data.player1 && data.player2) {
			dataToSave = {
				...dataToSave,
				player1: data.player1,
				player2: data.player2
			};
		}

		// Si recibimos IDs de jugadores, guardarlos
		if (data.player1_id && data.player2_id) {
			dataToSave = {
				...dataToSave,
				player1_id: data.player1_id,
				player2_id: data.player2_id
			};
		}

		this.saveGameData(this.gameId, dataToSave);

		diagnosticService.debug('GameReconnection', 'Game data saved', dataToSave);

		if (this.callbacks.onReconnect) {
			this.callbacks.onReconnect(data);
		}
	}

	// Muestra UI para intentos de reconexión
	showReconnectionAttempt(attempt, max) {
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

			// Añadir diagnóstico
			const diagnosticButton = document.createElement('button');
			diagnosticButton.textContent = 'Diagnóstico';
			diagnosticButton.className = 'btn btn-sm btn-outline-info mt-3';
			diagnosticButton.onclick = () => {
				diagnosticService.showDiagnosticPanel();
			};

			reconnectOverlay.appendChild(spinner);
			reconnectOverlay.appendChild(message);
			reconnectOverlay.appendChild(diagnosticButton);

			// Buscar el wrapper del juego
			const gameWrapper = document.querySelector('.game-wrapper');
			if (gameWrapper) {
				gameWrapper.appendChild(reconnectOverlay);
			} else {
				document.body.appendChild(reconnectOverlay);
			}
		}

		document.getElementById('reconnectMessage').textContent =
			`Reconectando... (${attempt}/${max})`;
	}

	// Muestra UI para reconexión exitosa
	showReconnectionSuccess() {
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

	// Muestra UI para reconexión fallida
	showReconnectionFailed() {
		const reconnectOverlay = document.getElementById('reconnectOverlay');
		if (reconnectOverlay) {
			reconnectOverlay.style.backgroundColor = 'rgba(128, 0, 0, 0.7)';
			document.getElementById('reconnectMessage').textContent =
				'No se pudo reconectar. La partida se ha perdido.';

			// Añadir botón para volver al lobby
			const backButton = document.createElement('button');
			backButton.className = 'btn btn-light mt-3 me-2';
			backButton.textContent = 'Volver al menú';
			backButton.onclick = () => window.location.href = '/game';

			// Añadir botón de diagnóstico
			const diagnosticButton = document.createElement('button');
			diagnosticButton.textContent = 'Ver diagnóstico';
			diagnosticButton.className = 'btn btn-info mt-3';
			diagnosticButton.onclick = () => {
				diagnosticService.showDiagnosticPanel();
			};

			reconnectOverlay.appendChild(backButton);
			reconnectOverlay.appendChild(diagnosticButton);
		}
	}

	// Maneja desconexión del oponente
	handleOpponentDisconnect(data) {
		const opponentSide = data.side;

		diagnosticService.info('GameReconnection', 'Opponent disconnected', {
			side: opponentSide,
			playerId: data.player_id
		});

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
		statusEl.style.zIndex = '100';

		const wrapper = document.querySelector('.game-wrapper');
		if (wrapper) {
			wrapper.appendChild(statusEl);

			// Remover el mensaje después de 5 segundos
			setTimeout(() => {
				if (statusEl.parentNode) {
					statusEl.remove();
				}
			}, 5000);
		}
	}

	// Maneja reconexión del oponente
	handleOpponentReconnect(data) {
		const opponentSide = data.side;
		const opponentName = data.username;

		diagnosticService.info('GameReconnection', 'Opponent reconnected', {
			side: opponentSide,
			playerId: data.player_id,
			username: opponentName
		});

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
		statusEl.style.zIndex = '100';

		const wrapper = document.querySelector('.game-wrapper');
		if (wrapper) {
			wrapper.appendChild(statusEl);

			// Remover el mensaje después de 5 segundos
			setTimeout(() => {
				if (statusEl.parentNode) {
					statusEl.remove();
				}
			}, 5000);
		}
	}

	// Guarda datos del juego en localStorage
	saveGameData(gameId, data) {
		try {
			localStorage.setItem(`game_${gameId}`, JSON.stringify(data));
			diagnosticService.debug('GameReconnection', 'Game data saved', data);
		} catch (e) {
			diagnosticService.error('GameReconnection', 'Error saving game data', e);
		}
	}

	// Recupera datos del juego de localStorage
	getSavedGameData(gameId) {
		try {
			const savedData = localStorage.getItem(`game_${gameId}`);
			return savedData ? JSON.parse(savedData) : null;
		} catch (e) {
			diagnosticService.error('GameReconnection', 'Error retrieving game data', e);
			return null;
		}
	}

	// Añadir un nuevo método para recuperar datos de reconexión de forma más robusta

	/**
	 * Intenta recuperar datos de reconexión con mayor resiliencia
	 */
	recoverReconnectionData(gameId) {
		try {
			const savedData = this.getSavedGameData(gameId);
			if (savedData) {
				this.playerSide = savedData.playerSide || this.playerSide;
				this.reconnecting = true;

				// También recuperar usuarios si es posible
				if (savedData.player1) {
					this.player1 = savedData.player1;
				}
				if (savedData.player2) {
					this.player2 = savedData.player2;
				}

				diagnosticService.info('GameReconnection', 'Datos de reconexión recuperados exitosamente', {
					playerSide: this.playerSide,
					reconnecting: this.reconnecting
				});
				return true;
			}
			return false;
		} catch (error) {
			diagnosticService.error('GameReconnection', 'Error recuperando datos de reconexión', error);
			return false;
		}
	}

	// Optimización para envío de mensajes críticos
	send(message) {
		if (this.socket && this.socket.readyState === WebSocket.OPEN) {
			// Añadir timestamp a todos los mensajes si no lo tienen ya
			if (!message.timestamp) {
				message.timestamp = Date.now();
			}

			// Añadir ID de conexión
			if (!message.connectionId) {
				message.connectionId = this.connectionId;
			}

			// Optimización para evitar envíos duplicados de comandos de parada
			const isStopCommand = message.force_stop || message.type === 'force_stop';

			if (isStopCommand) {
				// Añadir identificador único si no existe
				message.message_id = message.message_id || `stop_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

				// Verificar si acabamos de enviar un comando similar
				const now = Date.now();
				if (this._lastStopCommandTime && (now - this._lastStopCommandTime < 50)) {
					// Omitir este comando si acabamos de enviar uno similar en los últimos 50ms
					diagnosticService.trace('GameReconnection', 'Omitiendo comando de parada duplicado', {
						timestamp: message.timestamp,
						timeSinceLastStop: now - this._lastStopCommandTime
					});
					return;
				}

				// Registrar tiempo del último comando de parada
				this._lastStopCommandTime = now;

				diagnosticService.debug('GameReconnection', 'Sending force stop', {
					side: message.side,
					timestamp: message.timestamp,
					message_id: message.message_id
				});
			}

			// Enviar mensaje
			try {
				const messageStr = JSON.stringify(message);
				this.socket.send(messageStr);

				// OPTIMIZACIÓN: Para mensajes críticos solo enviar un retry si no es de fast reconnect
				if (isStopCommand && message.critical && !message.type.includes('fast_reconnect')) {
					setTimeout(() => {
						if (this.socket && this.socket.readyState === WebSocket.OPEN) {
							message.timestamp = Date.now();
							message.retry = true;
							message.message_id = `retry_${message.message_id}`;
							this.socket.send(JSON.stringify(message));
							diagnosticService.trace('GameReconnection', 'Sent retry force stop message', {
								message_id: message.message_id
							});
						}
					}, 25);  // Mantener en 25ms para mensajes críticos
				}
			} catch (error) {
				diagnosticService.error('GameReconnection', 'Error sending message', {
					error,
					message
				});
			}
		} else {
			diagnosticService.warn('GameReconnection', 'Cannot send message, socket not open', {
				socketState: this.socket?.readyState,
				message
			});
		}
	}

	// Nuevo método para manejar el protocolo Fast Reconnect
	handleFastReconnect(data) {
		diagnosticService.info('GameReconnection', 'Fast reconnect successful', {
			playerSide: data.player_side || this.playerSide,
			timestamp: data.timestamp
		});

		this.reconnecting = false;
		this.reconnectAttempts = 0;

		diagnosticService.connectionEvent('fast_reconnect', {
			gameId: this.gameId,
			connectionId: this.connectionId
		});

		// Inmediatamente procesar los datos sin esperas
		// Si el servidor nos envía información del lado del jugador, usarla
		if (data.player_side) {
			this.playerSide = data.player_side;
		}

		// OPTIMIZACIÓN: Enviar un único comando de parada para evitar duplicados
		if (this.playerSide && this.socket && this.socket.readyState === WebSocket.OPEN) {
			const userId = localStorage.getItem('user_id');
			const stopCommand = {
				type: 'move_paddle',
				direction: 0,
				side: this.playerSide,
				player_id: parseInt(userId),
				timestamp: Date.now(),
				force_stop: true,
				critical: true,
				message_id: `fast_reconnect_stop_${Date.now()}`
			};

			diagnosticService.info('GameReconnection', 'Enviando comando de parada para fast reconnect');
			this.send(stopCommand);
		}

		// Guardar o actualizar datos
		const existingData = this.getSavedGameData(this.gameId) || {};

		let dataToSave = {
			...existingData,
			playerSide: this.playerSide,
			lastReconnection: Date.now()
		};

		this.saveGameData(this.gameId, dataToSave);
		diagnosticService.debug('GameReconnection', 'Game data saved', dataToSave);

		// Notificar reconexión exitosa
		if (this.callbacks.onFastReconnect) {
			this.callbacks.onFastReconnect(data);
		} else if (this.callbacks.onReconnect) {
			this.callbacks.onReconnect(data);
		}
	}

	// Nuevo método para manejar datos de predicción 
	handlePredictionData(data) {
		diagnosticService.debug('GameReconnection', 'Received prediction data');

		if (this.callbacks.onPredictionData) {
			this.callbacks.onPredictionData(data);
		}
	}

	// Cierra la conexión
	disconnect() {
		diagnosticService.info('GameReconnection', 'Manually disconnecting');
		if (this.socket) {
			try {
				// Detener health check
				if (this.heartbeatInterval) {
					clearInterval(this.heartbeatInterval);
					this.heartbeatInterval = null;
				}

				// Cerrar socket
				if (this.socket.readyState === WebSocket.OPEN ||
					this.socket.readyState === WebSocket.CONNECTING) {
					this.socket.close(1000, 'Vista desmontada');
				}
				this.socket = null;
				diagnosticService.debug('GameReconnection', 'Socket closed successfully');
			} catch (e) {
				diagnosticService.error('GameReconnection', 'Error disconnecting socket', e);
			}
		}
	}

	// Obtiene el lado del jugador
	getPlayerSide() {
		return this.playerSide;
	}

	// Exporta un reporte de diagnóstico completo específico para el juego
	exportGameDiagnostics() {
		const report = {
			...diagnosticService.getDiagnosticReport(),
			gameSpecific: {
				gameId: this.gameId,
				playerSide: this.playerSide,
				reconnecting: this.reconnecting,
				reconnectAttempts: this.reconnectAttempts,
				connectionId: this.connectionId,
				lastMessageTime: this.lastMessageTime,
				healthCheckEvents: [...this.healthCheckEvents],
				savedGameData: this.getSavedGameData(this.gameId)
			}
		};

		const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);

		const a = document.createElement('a');
		a.href = url;
		a.download = `game-diagnostic-${this.gameId}-${Date.now()}.json`;
		document.body.appendChild(a);
		a.click();

		setTimeout(() => {
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		}, 0);

		return report;
	}
}

export const gameReconnectionService = new GameReconnectionService();
