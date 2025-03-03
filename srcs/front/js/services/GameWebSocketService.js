import AuthService from './AuthService.js';
import { soundService } from './SoundService.js';

class GameWebSocketService {
    constructor() {
        this.socket = null;
        this.statusCallback = null;
        this.isSearching = false;
    }

    async setupConnection(statusCallback) {
        this.statusCallback = statusCallback;
        
        // Verificar si ya estaba buscando partida
        this.isSearching = localStorage.getItem('matchmaking_active') === 'true';

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
            
            // Si estaba buscando partida, reanudar búsqueda
            if (this.isSearching) {
                this.updateStatus('Reanudando búsqueda...');
                this.send({
                    type: 'find_match',
                    user_id: userId
                });
            } else {
                this.updateStatus('Buscando oponente...');
            }
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📩 Mensaje:', data);
                
                switch(data.status) {
                    case 'waiting':
                    case 'searching':
                        this.isSearching = true;
                        localStorage.setItem('matchmaking_active', 'true');
                        this.updateStatus('Buscando oponente...');
                        break;
                    case 'matched':
                        this.handleMatch(data);
                        break;
                    case 'error':
                        this.isSearching = false;
                        localStorage.removeItem('matchmaking_active');
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
            // Si estaba buscando y se cierra la conexión, intentar reconectar
            if (this.isSearching) {
                console.log('🔄 Reconectando...');
                this.updateStatus('Reconectando...');
                setTimeout(() => this.setupConnection(this.statusCallback), 1000);
            }
            console.log('❌ Conexión cerrada:', event.code);
            this.updateStatus('Conexión cerrada');
        };

        this.socket.onerror = (error) => {
            console.error('🚫 Error en conexión:', error);
            this.updateStatus('Error de conexión');
        };
    }

    async handleMatch(data) {
        this.isSearching = false;
        localStorage.removeItem('matchmaking_active');
        
        // Solo reproducir el sonido y redirigir
        try {
            await soundService.playMatchFound();
        } catch (e) {
            console.log('Audio no soportado');
        }
        
        // Redirección inmediata
        window.history.pushState(null, '', `/game/${data.game_id}`);
        window.dispatchEvent(new PopStateEvent('popstate'));
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

    async disconnect() {
        console.log('Desconectando del matchmaking...');
        this.isSearching = false;
        localStorage.removeItem('matchmaking_active');
        
        if (this.socket) {
            try {
                this.socket.close(1000, 'User cancelled matchmaking');
                this.socket = null;
                console.log('Desconexión exitosa');
                return true;
            } catch (error) {
                console.error('Error al desconectar:', error);
                throw error;
            }
        }
        return false;
    }
}

export const gameWebSocketService = new GameWebSocketService();
