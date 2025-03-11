/**
 * Servicio para diagnóstico y logging de problemas
 */
class DiagnosticService {
	constructor() {
		// Configurar nivel de log (1: Error, 2: Warn, 3: Info, 4: Debug, 5: Trace)
		this.logLevel = 5;

		// Mantener un buffer de los últimos logs para debug
		this.logBuffer = [];
		this.maxBufferSize = 200;

		// Métricas de conexión
		this.connectionMetrics = {
			attempts: 0,
			successes: 0,
			failures: 0,
			disconnects: 0,
			reconnects: 0,
			lastEvent: null
		};

		// Objeto para seguir websockets activos
		this.activeConnections = {};
	}

	/**
	 * Registra un mensaje de error
	 * @param {string} source - Origen del error (componente)
	 * @param {string} message - Mensaje descriptivo
	 * @param {Error|Object} [error] - Objeto de error o información adicional
	 */
	error(source, message, error = null) {
		if (this.logLevel >= 1) {
			const entry = this._createLogEntry('ERROR', source, message, error);
			this._addToBuffer(entry);
			console.error(`[ERROR][${source}] ${message}`, error);
		}
	}

	/**
	 * Registra un mensaje de advertencia
	 * @param {string} source - Origen de la advertencia
	 * @param {string} message - Mensaje descriptivo
	 * @param {Object} [data] - Datos adicionales
	 */
	warn(source, message, data = null) {
		if (this.logLevel >= 2) {
			const entry = this._createLogEntry('WARN', source, message, data);
			this._addToBuffer(entry);
			console.warn(`[WARN][${source}] ${message}`, data);
		}
	}

	/**
	 * Registra un mensaje informativo
	 * @param {string} source - Origen del mensaje
	 * @param {string} message - Mensaje descriptivo
	 * @param {Object} [data] - Datos adicionales
	 */
	info(source, message, data = null) {
		if (this.logLevel >= 3) {
			const entry = this._createLogEntry('INFO', source, message, data);
			this._addToBuffer(entry);
			console.info(`[INFO][${source}] ${message}`, data);
		}
	}

	/**
	 * Registra un mensaje de depuración
	 * @param {string} source - Origen del mensaje
	 * @param {string} message - Mensaje descriptivo
	 * @param {Object} [data] - Datos adicionales
	 */
	debug(source, message, data = null) {
		if (this.logLevel >= 4) {
			const entry = this._createLogEntry('DEBUG', source, message, data);
			this._addToBuffer(entry);
			console.debug(`[DEBUG][${source}] ${message}`, data);
		}
	}

	/**
	 * Registra un mensaje de traza con mayor nivel de detalle
	 * @param {string} source - Origen del mensaje
	 * @param {string} message - Mensaje descriptivo
	 * @param {Object} [data] - Datos adicionales
	 */
	trace(source, message, data = null) {
		if (this.logLevel >= 5) {
			const entry = this._createLogEntry('TRACE', source, message, data);
			this._addToBuffer(entry);
			console.debug(`[TRACE][${source}] ${message}`, data);
		}
	}

	/**
	 * Registra un evento de conexión WebSocket
	 * @param {string} action - Tipo de evento (connect, disconnect, etc)
	 * @param {Object} details - Detalles del evento
	 */
	connectionEvent(action, details) {
		const metrics = this.connectionMetrics;
		const timestamp = new Date();
		let metricUpdated = false;

		switch (action) {
			case 'attempt':
				metrics.attempts++;
				metricUpdated = true;
				break;
			case 'success':
				metrics.successes++;
				metricUpdated = true;
				break;
			case 'failure':
				metrics.failures++;
				metricUpdated = true;
				break;
			case 'disconnect':
				metrics.disconnects++;
				metricUpdated = true;
				break;
			case 'reconnect':
				metrics.reconnects++;
				metricUpdated = true;
				break;
		}

		if (metricUpdated) {
			metrics.lastEvent = {
				action,
				timestamp,
				details
			};
		}

		this.info('Connection', `${action} - ${JSON.stringify(details)}`);
	}

	/**
	 * Registra una nueva conexión WebSocket
	 * @param {WebSocket} socket - Objeto WebSocket
	 * @param {string} id - Identificador único para esta conexión
	 */
	trackWebSocket(socket, id) {
		if (!socket) return;

		const connectionInfo = {
			id,
			createdAt: new Date(),
			readyState: socket.readyState,
			events: []
		};

		// Guardar referencia
		this.activeConnections[id] = connectionInfo;

		// Monitorear eventos
		const trackEvent = (event, details = {}) => {
			connectionInfo.events.push({
				type: event,
				timestamp: new Date(),
				readyState: socket.readyState,
				...details
			});
			connectionInfo.readyState = socket.readyState;
		};

		// Añadir listeners
		socket.addEventListener('open', () => {
			trackEvent('open');
			this.connectionEvent('success', { id });
		});

		socket.addEventListener('close', (event) => {
			trackEvent('close', {
				code: event.code,
				reason: event.reason,
				wasClean: event.wasClean
			});
			this.connectionEvent('disconnect', {
				id,
				code: event.code,
				reason: event.reason
			});

			// Limpiar después de cerrar
			delete this.activeConnections[id];
		});

		socket.addEventListener('error', () => {
			trackEvent('error');
			this.connectionEvent('failure', { id });
		});

		socket.addEventListener('message', () => {
			trackEvent('message');
		});

		return connectionInfo;
	}

	/**
	 * Obtiene el estado actual de diagnóstico completo
	 */
	getDiagnosticReport() {
		return {
			timestamp: new Date(),
			buffer: [...this.logBuffer],
			metrics: { ...this.connectionMetrics },
			connections: { ...this.activeConnections },
			userAgent: navigator.userAgent,
			url: window.location.href,
			networkType: navigator.connection ? navigator.connection.effectiveType : 'unknown'
		};
	}

	/**
	 * Exporta el reporte de diagnóstico como JSON
	 */
	exportDiagnosticReport() {
		const report = this.getDiagnosticReport();
		const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);

		const a = document.createElement('a');
		a.href = url;
		a.download = `diagnostic-report-${new Date().toISOString()}.json`;
		document.body.appendChild(a);
		a.click();

		setTimeout(() => {
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		}, 0);
	}

	/**
	 * Crea un registro en formato estándar
	 */
	_createLogEntry(level, source, message, data) {
		return {
			timestamp: new Date().toISOString(),
			level,
			source,
			message,
			data: data || null
		};
	}

	/**
	 * Añade un registro al buffer, manteniendo el tamaño máximo
	 */
	_addToBuffer(entry) {
		this.logBuffer.push(entry);
		if (this.logBuffer.length > this.maxBufferSize) {
			this.logBuffer.shift();
		}
	}

	/**
	 * Muestra un panel de diagnóstico en la UI
	 */
	showDiagnosticPanel() {
		// Verificar si ya existe
		let panel = document.getElementById('diagnostic-panel');

		if (!panel) {
			panel = document.createElement('div');
			panel.id = 'diagnostic-panel';
			panel.style.cssText = `
                position: fixed;
                bottom: 10px;
                right: 10px;
                width: 300px;
                max-height: 400px;
                background: rgba(0,0,0,0.8);
                color: #0f0;
                border: 1px solid #0f0;
                font-family: monospace;
                font-size: 12px;
                padding: 10px;
                overflow-y: auto;
                z-index: 9999;
            `;

			const header = document.createElement('div');
			header.innerHTML = `
                <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                    <strong>Diagnostic Panel</strong>
                    <span>
                        <button id="export-diagnostic" style="background:#333;color:#0f0;border:1px solid #0f0;margin-right:5px">Export</button>
                        <button id="close-diagnostic" style="background:#333;color:#0f0;border:1px solid #0f0">X</button>
                    </span>
                </div>
            `;

			const content = document.createElement('div');
			content.id = 'diagnostic-content';

			panel.appendChild(header);
			panel.appendChild(content);
			document.body.appendChild(panel);

			// Event listeners
			document.getElementById('close-diagnostic').addEventListener('click', () => {
				panel.remove();
			});

			document.getElementById('export-diagnostic').addEventListener('click', () => {
				this.exportDiagnosticReport();
			});
		}

		// Actualizar contenido
		const content = document.getElementById('diagnostic-content');
		const report = this.getDiagnosticReport();

		const connectionStatus = Object.keys(this.activeConnections).length > 0
			? 'ACTIVE' : 'NONE';

		content.innerHTML = `
            <div style="margin-bottom:10px">
                <div><strong>WebSockets:</strong> ${connectionStatus}</div>
                <div><strong>Attempts:</strong> ${report.metrics.attempts}</div>
                <div><strong>Successes:</strong> ${report.metrics.successes}</div>
                <div><strong>Failures:</strong> ${report.metrics.failures}</div>
                <div><strong>Disconnects:</strong> ${report.metrics.disconnects}</div>
                <div><strong>Reconnects:</strong> ${report.metrics.reconnects}</div>
            </div>
            <div><strong>Recent Events:</strong></div>
            <div style="max-height:200px;overflow-y:auto">
                ${this.logBuffer.slice(-10).map(log =>
			`<div style="color:${this._getColorForLevel(log.level)}">[${log.level}] ${log.message}</div>`
		).join('')}
            </div>
        `;

		// Programar actualización
		setTimeout(() => {
			if (document.getElementById('diagnostic-panel')) {
				this.updateDiagnosticPanel();
			}
		}, 2000);
	}

	updateDiagnosticPanel() {
		const panel = document.getElementById('diagnostic-panel');
		if (panel) {
			this.showDiagnosticPanel();
		}
	}

	_getColorForLevel(level) {
		switch (level) {
			case 'ERROR': return '#f44';
			case 'WARN': return '#fa2';
			case 'INFO': return '#2af';
			case 'DEBUG': return '#2f2';
			case 'TRACE': return '#aaa';
			default: return '#fff';
		}
	}
}

export const diagnosticService = new DiagnosticService();
