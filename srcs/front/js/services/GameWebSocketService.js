import AuthService from './AuthService.js';

class GameWebSocketService {
    constructor() {
        this.socket = null;
        this.statusCallback = null;
    }

    async setupConnection(statusCallback) {
        this.statusCallback = statusCallback;
        
        // Obtener user_id antes de conectar
        const userId = await AuthService.getUserId();
        if (!userId) {
            console.error('No se pudo obtener el ID del usuario');
            return;
        }

        console.log('User ID obtenido:', userId);
        localStorage.setItem('user_id', userId);  // Guardar para uso futuro

        const baseUrl = window.location.origin.replace('http:', 'ws:').replace('https:', 'wss:');
        const wsUrl = `${baseUrl}/ws/matchmaking/`;

        console.log('🔄 Conectando a matchmaking:', wsUrl);
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('✅ Conectado al matchmaking');
            this.updateStatus('Buscando oponente...');
            // Enviar mensaje de búsqueda de partida
            this.send({
                type: 'find_match',
                user_id: userId  // Enviar el user_id aquí
            });
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📩 Mensaje:', data);
                
                switch(data.status) {
                    case 'waiting':
                        this.updateStatus('En cola de espera...');
                        break;
                    case 'searching':
                        this.updateStatus('Buscando oponente...');
                        break;
                    case 'matched':
                        this.updateStatus('¡Partida encontrada!');
                        console.log('🎮 Redirigiendo a partida:', data.game_id);
                        // Usamos pushState en lugar de window.location
                        window.history.pushState(null, '', `/game/${data.game_id}`);
                        window.dispatchEvent(new PopStateEvent('popstate'));
                        break;
                    case 'error':
                        this.updateStatus(`Error: ${data.message}`);
                        break;
                    default:
                        console.log('Estado no manejado:', data);
                }
            } catch (error) {
                console.error('Error al procesar mensaje:', error);
            }
        };

        this.socket.onclose = (event) => {
            console.log('❌ Conexión cerrada:', event.code);
            this.updateStatus('Conexión cerrada');
        };

        this.socket.onerror = (error) => {
            console.error('🚫 Error en conexión:', error);
            this.updateStatus('Error de conexión');
        };
    }

    send(message) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            console.log('📤 Enviando:', message);
            this.socket.send(JSON.stringify(message));
        } else {
            console.warn('⚠️ Socket no está listo');
        }
    }

    updateStatus(message) {
        if (this.statusCallback) {
            this.statusCallback(message);
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

export const gameWebSocketService = new GameWebSocketService();
