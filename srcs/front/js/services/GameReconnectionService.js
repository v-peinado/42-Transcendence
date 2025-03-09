class GameReconnectionService {
	constructor() {
		this.socket = null;
		this.gameId = null;
		this.playerSide = null;
		this.reconnecting = false;
		this.reconnectAttempts = 0;
		this.MAX_RECONNECT_ATTEMPTS = 15;
		this.RECONNECT_INTERVAL = 2000;
	}

	// Configura la conexión WebSocket y maneja reconexiones
	setupConnection(gameId, callbacks = {}) {
		this.gameId = gameId;
		this.callbacks = callbacks;
		const userId = localStorage.getItem('user_id');

		// Recuperar datos guardados si existen
		const savedData = this.getSavedGameData(gameId);
		if (savedData) {
			this.playerSide = savedData.playerSide;
			this.reconnecting = true;
			console.log('Recuperando datos de sesión anterior. Lado del jugador:', this.playerSide);
		}

		// Crear conexión WebSocket
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws/game/${gameId}/`;
		console.log('Conectando a:', wsUrl, 'Reconectando:', this.reconnecting);

		// Cerrar socket existente si hubiera
		if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
			this.socket.close();
		}

		this.socket = new WebSocket(wsUrl);

		this.socket.onopen = () => {
			console.log('Conexión WebSocket establecida. Reconexión:', this.reconnecting);
			if (this.callbacks.onOpen) {
				this.callbacks.onOpen(this.reconnecting);
			}

			// Si estamos reconectando, solicitar estado actual del juego
			if (this.reconnecting) {
				console.log('Solicitando estado del juego al servidor...');
				setTimeout(() => {
					if (this.socket && this.socket.readyState === WebSocket.OPEN) {
						this.socket.send(JSON.stringify({
							type: 'request_game_state',
							player_id: parseInt(userId),
							game_id: parseInt(gameId)
						}));
						console.log('Solicitud de estado enviada');
					}
				}, 800);
			}
		};

		this.socket.onmessage = (event) => {
			const data = JSON.parse(event.data);

			// Para reconexión
			if (data.type === 'game_state' && (data.is_reconnection || this.reconnecting)) {
				this.handleReconnectionSuccess(data);
			} else if (data.type === 'player_disconnected') {
				this.handleOpponentDisconnect(data);
			} else if (data.type === 'player_reconnected') {
				this.handleOpponentReconnect(data);
			}

			// Pasar el mensaje al callback
			if (this.callbacks.onMessage) {
				this.callbacks.onMessage(data);
			}
		};

		this.socket.onclose = (event) => {
			console.log('Conexión cerrada', event);
			// Solo intentar reconectar si no fue un cierre controlado
			if (event.code !== 1000 && !document.getElementById('gameOverScreen').style.display === 'flex') {
				this.handleDisconnection();
			}
		};

		this.socket.onerror = (error) => {
			console.error('Error en WebSocket:', error);
			this.handleDisconnection();
		};

		return this.socket;
	}

	// Maneja la desconexión e intenta reconectar
	handleDisconnection() {
		if (this.reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
			console.log('Máximo de intentos de reconexión alcanzado.');
			this.showReconnectionFailed();
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

		// Mostrar estado de reconexión
		this.showReconnectionAttempt(this.reconnectAttempts, this.MAX_RECONNECT_ATTEMPTS);

		// Intentar reconectar después de intervalo
		setTimeout(() => {
			if (this.reconnecting) {
				this.setupConnection(this.gameId, this.callbacks);
			}
		}, this.RECONNECT_INTERVAL);
	}

	// Maneja la reconexión exitosa
	handleReconnectionSuccess(data) {
		this.reconnecting = false;
		this.reconnectAttempts = 0;

		// Si el servidor nos envía información del lado del jugador, usarla
		if (data.player_side) {
			this.playerSide = data.player_side;
			console.log('Lado del jugador recibido del servidor:', this.playerSide);

			// Guardar o actualizar datos
			const existingData = this.getSavedGameData(this.gameId) || {};
			this.saveGameData(this.gameId, {
				...existingData,
				playerSide: data.player_side
			});
		}

		// Si recibimos nombres de jugadores, guardarlos
		if (data.player1 && data.player2) {
			const existingData = this.getSavedGameData(this.gameId) || {};
			this.saveGameData(this.gameId, {
				...existingData,
				player1: data.player1,
				player2: data.player2
			});
		}

		this.showReconnectionSuccess();

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

			reconnectOverlay.appendChild(spinner);
			reconnectOverlay.appendChild(message);

			document.querySelector('.game-wrapper').appendChild(reconnectOverlay);
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
			backButton.className = 'btn btn-light mt-3';
			backButton.textContent = 'Volver al menú';
			backButton.onclick = () => window.location.href = '/game';
			reconnectOverlay.appendChild(backButton);
		}
	}

	// Maneja desconexión del oponente
	handleOpponentDisconnect(data) {
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

	// Maneja reconexión del oponente
	handleOpponentReconnect(data) {
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

	// Guarda datos del juego en localStorage
	saveGameData(gameId, data) {
		try {
			localStorage.setItem(`game_${gameId}`, JSON.stringify(data));
			console.log('Datos de juego guardados:', data);
		} catch (e) {
			console.error('Error al guardar datos de juego:', e);
		}
	}

	// Recupera datos del juego de localStorage
	getSavedGameData(gameId) {
		try {
			const savedData = localStorage.getItem(`game_${gameId}`);
			return savedData ? JSON.parse(savedData) : null;
		} catch (e) {
			console.error('Error al recuperar datos de juego:', e);
			return null;
		}
	}

	// Envía un mensaje por el WebSocket
	send(message) {
		if (this.socket && this.socket.readyState === WebSocket.OPEN) {
			this.socket.send(JSON.stringify(message));
		}
	}

	// Cierra la conexión
	disconnect() {
		if (this.socket && this.socket.readyState === WebSocket.OPEN) {
			this.socket.close(1000, 'Vista desmontada');
			this.socket = null;
		}
	}

	// Obtiene el lado del jugador
	getPlayerSide() {
		return this.playerSide;
	}
}

export const gameReconnectionService = new GameReconnectionService();
