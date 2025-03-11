class GameReconnectionService {
	constructor() {
		this.socket = null;
		this.gameId = null;
		this.playerSide = null;
		this.reconnecting = false;
		this.reconnectAttempts = 0;
		this.MAX_RECONNECT_ATTEMPTS = 15;
		this.RECONNECT_INTERVAL = 2000;
		this.lastMessageTime = Date.now();
		this._lastStopCommandTime = 0;
	}

	// Configura conexión WebSocket con soporte para reconexión rápida
	setupConnection(gameId, callbacks = {}) {
		this.gameId = gameId;
		this.callbacks = callbacks;

		console.log(`Setting up connection for game ${gameId}`);

		const userId = localStorage.getItem('user_id');

		// Recuperar datos de reconexión
		this.recoverReconnectionData(gameId);

		// Crear conexión WebSocket
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws/game/${gameId}/`;

		// Cerrar socket existente
		if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
			try {
				this.socket.close(1000, 'Creando nueva conexión');
			} catch (e) {
				console.error('Error closing socket:', e);
			}
		}

		try {
			this.socket = new WebSocket(wsUrl);

			this.socket.onopen = () => {
				console.log('WebSocket connection established');

				if (this.callbacks.onOpen) {
					this.callbacks.onOpen(this.reconnecting);
				}

				// Si estamos reconectando, implementar protocolo FAST RECONNECT
				if (this.reconnecting && this.playerSide) {
					console.log('Iniciando protocolo de reconexión rápida');

					// Enviar petición de reconexión rápida
					this.send({
						type: 'fast_reconnect',
						player_id: parseInt(userId),
						game_id: parseInt(gameId),
						side: this.playerSide,
						timestamp: Date.now()
					});

					// Como respaldo, enviar también una solicitud estándar después de un breve retraso
					setTimeout(() => {
						if (this.socket && this.socket.readyState === WebSocket.OPEN) {
							this.send({
								type: 'request_game_state',
								player_id: parseInt(userId),
								game_id: parseInt(gameId),
								timestamp: Date.now()
							});
						}
					}, 200);
				}
			};

			this.socket.onmessage = (event) => {
				// Actualizar timestamp
				this.lastMessageTime = Date.now();

				// Procesar mensaje
				try {
					const data = JSON.parse(event.data);

					// Manejar tipos de mensajes específicos para reconexión
					if (data.type === 'fast_state') {
						this.handleFastReconnect(data);
					} else if (data.type === 'game_state' && (data.is_reconnection || this.reconnecting)) {
						this.handleReconnectionSuccess(data);
					}

					// Pasar mensaje al callback
					if (this.callbacks.onMessage) {
						this.callbacks.onMessage(data);
					}
				} catch (error) {
					console.error('Error processing message:', error);
				}
			};

			this.socket.onclose = (event) => {
				console.log('Connection closed', event.code, event.reason);

				// Solo intentar reconectar si no fue un cierre controlado
				if (event.code !== 1000) {
					this.handleDisconnection();
				}
			};

			this.socket.onerror = () => {
				console.error('WebSocket error');
				this.handleDisconnection();
			};
		} catch (error) {
			console.error('Error creating WebSocket:', error);
			this.handleDisconnection();
		}

		return this.socket;
	}

	// Maneja desconexión e intenta reconectar
	handleDisconnection() {
		if (this.reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
			console.warn('Maximum reconnection attempts reached');
			if (this.callbacks.onReconnectFailed) {
				this.callbacks.onReconnectFailed();
			}
			return;
		}

		this.reconnecting = true;
		this.reconnectAttempts++;

		if (this.callbacks.onDisconnect) {
			this.callbacks.onDisconnect(this.reconnectAttempts, this.MAX_RECONNECT_ATTEMPTS);
		}

		// Intentar reconectar después de intervalo
		setTimeout(() => {
			if (this.reconnecting) {
				console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.MAX_RECONNECT_ATTEMPTS})`);
				this.setupConnection(this.gameId, this.callbacks);
			}
		}, this.RECONNECT_INTERVAL);
	}

	// Manejo de reconexión rápida
	handleFastReconnect(data) {
		console.log('Fast reconnect successful');

		this.reconnecting = false;
		this.reconnectAttempts = 0;

		// Si el servidor envía información del lado del jugador, actualizarla
		if (data.player_side) {
			this.playerSide = data.player_side;
		}

		// Enviar un único comando de parada
		if (this.playerSide && this.socket && this.socket.readyState === WebSocket.OPEN) {
			const userId = localStorage.getItem('user_id');
			this.send({
				type: 'move_paddle',
				direction: 0,
				side: this.playerSide,
				player_id: parseInt(userId),
				timestamp: Date.now(),
				force_stop: true
			});
		}

		// Guardar datos
		this.saveGameData(this.gameId, {
			playerSide: this.playerSide,
			lastReconnection: Date.now()
		});

		// Notificar reconexión exitosa
		if (this.callbacks.onFastReconnect) {
			this.callbacks.onFastReconnect(data);
		} else if (this.callbacks.onReconnect) {
			this.callbacks.onReconnect(data);
		}
	}

	// Manejo de reconexión tradicional
	handleReconnectionSuccess(data) {
		console.log('Reconnection successful');

		this.reconnecting = false;
		this.reconnectAttempts = 0;

		// Actualizar lado del jugador
		if (data.player_side) {
			this.playerSide = data.player_side;
		}

		// Enviar comando de parada
		if (this.playerSide && this.socket && this.socket.readyState === WebSocket.OPEN) {
			const userId = localStorage.getItem('user_id');
			this.send({
				type: 'move_paddle',
				direction: 0,
				side: this.playerSide,
				player_id: parseInt(userId),
				timestamp: Date.now(),
				force_stop: true
			});
		}

		// Guardar datos
		const existingData = this.getSavedGameData(this.gameId) || {};
		let dataToSave = {
			...existingData,
			playerSide: this.playerSide,
			lastReconnection: Date.now()
		};

		// Guardar nombres e IDs de jugadores si están disponibles
		if (data.player1 && data.player2) {
			dataToSave.player1 = data.player1;
			dataToSave.player2 = data.player2;
		}
		if (data.player1_id && data.player2_id) {
			dataToSave.player1_id = data.player1_id;
			dataToSave.player2_id = data.player2_id;
		}

		this.saveGameData(this.gameId, dataToSave);

		if (this.callbacks.onReconnect) {
			this.callbacks.onReconnect(data);
		}
	}

	// Guarda datos en localStorage
	saveGameData(gameId, data) {
		try {
			localStorage.setItem(`game_${gameId}`, JSON.stringify(data));
		} catch (e) {
			console.error('Error saving game data:', e);
		}
	}

	// Recupera datos de localStorage
	getSavedGameData(gameId) {
		try {
			const savedData = localStorage.getItem(`game_${gameId}`);
			return savedData ? JSON.parse(savedData) : null;
		} catch (e) {
			console.error('Error retrieving game data:', e);
			return null;
		}
	}

	// Recupera datos de reconexión
	recoverReconnectionData(gameId) {
		try {
			const savedData = this.getSavedGameData(gameId);
			if (savedData) {
				this.playerSide = savedData.playerSide || this.playerSide;
				this.reconnecting = true;

				console.log(`Recovered reconnection data: playerSide=${this.playerSide}`);
				return true;
			}
			return false;
		} catch (error) {
			console.error('Error recovering reconnection data:', error);
			return false;
		}
	}

	// Envía mensaje evitando duplicados de comandos de parada
	send(message) {
		if (this.socket && this.socket.readyState === WebSocket.OPEN) {
			// Añadir timestamp si no existe
			if (!message.timestamp) {
				message.timestamp = Date.now();
			}

			// Optimización para evitar comandos de parada duplicados
			const isStopCommand = message.force_stop || message.type === 'force_stop';
			if (isStopCommand) {
				// Verificar si acabamos de enviar un comando similar
				const now = Date.now();
				if (this._lastStopCommandTime && (now - this._lastStopCommandTime < 50)) {
					// Omitir comando si acabamos de enviar uno similar en los últimos 50ms
					return;
				}

				// Registrar tiempo del comando
				this._lastStopCommandTime = now;
			}

			// Enviar mensaje
			try {
				this.socket.send(JSON.stringify(message));
			} catch (error) {
				console.error('Error sending message:', error);
			}
		} else {
			console.warn('Cannot send message, socket not open');
		}
	}

	// Cierra la conexión
	disconnect() {
		if (this.socket) {
			try {
				if (this.socket.readyState === WebSocket.OPEN ||
					this.socket.readyState === WebSocket.CONNECTING) {
					this.socket.close(1000, 'Vista desmontada');
				}
				this.socket = null;
			} catch (e) {
				console.error('Error disconnecting socket:', e);
			}
		}
	}

	// Obtiene el lado del jugador
	getPlayerSide() {
		return this.playerSide;
	}
}

export const gameReconnectionService = new GameReconnectionService();
