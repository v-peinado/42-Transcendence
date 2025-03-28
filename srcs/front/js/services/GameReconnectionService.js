class GameReconnectionService {
	constructor() { // Inicialize variables
		this.socket = null; // socket where the connection will be stored
		this.gameId = null;
		this.playerSide = null;
		this.reconnecting = false; // Variable to know if the connection is reconnecting
		this.reconnectAttempts = 0;
		this.MAX_RECONNECT_ATTEMPTS = 15;
		this.RECONNECT_INTERVAL = 2000; // ms
		this.lastMessageTime = Date.now(); // time from the last message received by the server
		this._lastStopCommandTime = 0; // Last stop command time to avoid jitter
	}

	// Config websockets connection for game with fast reconnect
	setupConnection(gameId, callbacks = {}) {
		this.gameId = gameId;
		this.callbacks = callbacks; // Callbacks to handle the connection 

		console.log(`Setting up connection for game ${gameId}`);

		const userId = localStorage.getItem('user_id');

		// Recover reconnection data
		this.recoverReconnectionData(gameId); // Recover data from localStorage

		// Websockets data for connection
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'; // Check if the protocol is https or http
		const wsUrl = `${protocol}//${window.location.host}/ws/game/${gameId}/`; // Websockets url

		// Close the connection if it is open or connecting before creating a new one
		if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
			try {
				this.socket.close(1000, 'Creando nueva conexión');
			} catch (e) {
				console.error('Error closing socket:', e);
			}
		}
		// Create a new connection with the server when the connection is closed
		try {
			this.socket = new WebSocket(wsUrl);

			this.socket.onopen = () => {
				console.log('WebSocket connection established');

				if (this.callbacks.onOpen) {
					this.callbacks.onOpen(this.reconnecting);
				}

				// If we are reconnecting, send a fast reconnect request
				if (this.reconnecting && this.playerSide) {
					console.log('Iniciando protocolo de reconexión rápida');

					// Send fast reconnect request
					this.send({
						type: 'fast_reconnect',
						player_id: parseInt(userId),
						game_id: parseInt(gameId),
						side: this.playerSide,
						timestamp: Date.now()
					});

					// fallback to full state request if no response in 200ms (to more long disconnects)
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
			// Handle messages
			this.socket.onmessage = (event) => {
				// Update last message time
				this.lastMessageTime = Date.now();

				// Parse message
				try {
					const data = JSON.parse(event.data);

					// Handle fast reconnect response and game state
					if (data.type === 'fast_state') {
						this.handleFastReconnect(data);
					} else if (data.type === 'game_state' && (data.is_reconnection || this.reconnecting)) {
						this.handleReconnectionSuccess(data);
					}

					// Send message to callback
					if (this.callbacks.onMessage) {
						this.callbacks.onMessage(data);
					}
				} catch (error) {
					console.error('Error processing message:', error);
				}
			};

			this.socket.onclose = (event) => {
				console.log('Connection closed', event.code, event.reason);

				// Handle disconnection if not a normal close event (like page unload)
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

	// Handle disconnection and reconnect attempts
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

		// Try to reconnect after a delay
		setTimeout(() => {
			if (this.reconnecting) {
				console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.MAX_RECONNECT_ATTEMPTS})`);
				this.setupConnection(this.gameId, this.callbacks);
			}
		}, this.RECONNECT_INTERVAL);
	}

	// Handle fast reconnect response
	handleFastReconnect(data) {
		console.log('Fast reconnect successful');

		this.reconnecting = false;
		this.reconnectAttempts = 0;

		// If server has assigned a side, update it
		if (data.player_side) {
			this.playerSide = data.player_side;
		}

		// Send stop command to server to prevent paddle from moving
		if (this.playerSide && this.socket && this.socket.readyState === WebSocket.OPEN) {
			const userId = localStorage.getItem('user_id');
			this.send({
				type: 'move_paddle',
				direction: 0,
				side: this.playerSide,
				player_id: parseInt(userId),
				timestamp: Date.now()
			});
		}

		// Save data
		this.saveGameData(this.gameId, {
			playerSide: this.playerSide,
			lastReconnection: Date.now()
		});

		// Send notification to callback
		if (this.callbacks.onFastReconnect) {
			this.callbacks.onFastReconnect(data);
		} else if (this.callbacks.onReconnect) {
			this.callbacks.onReconnect(data);
		}
	}

	// Handle reconnection success and update player side
	handleReconnectionSuccess(data) {
		console.log('Reconnection successful');

		this.reconnecting = false;
		this.reconnectAttempts = 0;

		// Player side has been assigned by the server
		if (data.player_side) {
			this.playerSide = data.player_side;
		}


		// Save data
		const existingData = this.getSavedGameData(this.gameId) || {};
		let dataToSave = {
			...existingData,
			playerSide: this.playerSide,
			lastReconnection: Date.now()
		};

		// Save player names and IDs if available in the response
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

	// Save game data to localStorage
	saveGameData(gameId, data) {
		try {
			localStorage.setItem(`game_${gameId}`, JSON.stringify(data));
		} catch (e) {
			console.error('Error saving game data:', e);
		}
	}

	// Recover saved game data from localStorage
	getSavedGameData(gameId) {
		try {
			const savedData = localStorage.getItem(`game_${gameId}`);
			return savedData ? JSON.parse(savedData) : null;
		} catch (e) {
			console.error('Error retrieving game data:', e);
			return null;
		}
	}

	// Recover reconnection data from localStorage
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

	// Send a message through the socket connection
	send(message) {
		if (this.socket && this.socket.readyState === WebSocket.OPEN) {
			// Add timestamp if not present
			if (!message.timestamp) {
				message.timestamp = Date.now();
			}

			// Avoid sending stop commands too frequently (prevent paddle jitter)
			const isStopCommand = message.force_stop || message.type === 'force_stop';
			if (isStopCommand) {
				// Verrify time between stop commands to avoid jitter
				const now = Date.now();
				if (this._lastStopCommandTime && (now - this._lastStopCommandTime < 50)) {
					// Avoid sending stop command too frequently
					return;
				}

				// timestamp of the last stop command
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

	// close the socket connection
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

	// Get the player side
	getPlayerSide() {
		return this.playerSide;
	}
}

export const gameReconnectionService = new GameReconnectionService();