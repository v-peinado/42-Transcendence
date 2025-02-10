class WebSocketService {
    constructor() {
        this.socket = null;
        this.listeners = new Map();
        this.keepAliveInterval = null;
    }

    async connect(roomName = 'general') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws/chat/${roomName}/`;

        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                //aqui podemos añadir un mensaje de bienvenida o algo
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    const listeners = this.listeners.get(data.type) || [];
                    listeners.forEach(callback => callback(data));
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            };

            this.socket.onclose = (event) => {
                if (this.keepAliveInterval) {
                    clearInterval(this.keepAliveInterval);
                }
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Error al crear WebSocket:', error);
        }

        return this.socket;
    }

    disconnect() {
        if (this.keepAliveInterval) {
            clearInterval(this.keepAliveInterval);
            this.keepAliveInterval = null;
        }
        if (this.socket) {
            this.socket.close(1000);
            this.socket = null;
        }
        // Limpiar listeners
        this.listeners.clear();
    }

    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const formattedMessage = {
                type: message.type,
                message: message.content || '',
                user_id: parseInt(localStorage.getItem('user_id')),
                username: localStorage.getItem('username')
            };

            // Si es un mensaje de chat, usar el channel_name proporcionado o construirlo
            if (message.type === 'chat_message') {
                formattedMessage.channel_name = message.channel_name || `chat_${message.room}`;
            } 
            // Si es para crear un canal privado, añadir IDs de usuarios
            else if (message.type === 'create_private_channel') {
                formattedMessage.user1_id = message.user1_id;
                formattedMessage.user2_id = message.user2_id;
            }
            
            console.log('Enviando mensaje formateado:', formattedMessage);
            this.socket.send(JSON.stringify(formattedMessage));
        } else {
            console.error('Socket no conectado');
        }
    }

    startKeepAlive() {
        this.keepAliveInterval = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ type: 'keepalive' }));
            }
        }, 30000);
    }

    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, []);
        }
        this.listeners.get(eventType).push(callback);
    }

    off(eventType, callback) {
        if (this.listeners.has(eventType)) {
            const callbacks = this.listeners.get(eventType);
            const index = callbacks.indexOf(callback);
            if (index !== -1) {
                callbacks.splice(index, 1);
            }
        }
    }
}

export const webSocketService = new WebSocketService();
