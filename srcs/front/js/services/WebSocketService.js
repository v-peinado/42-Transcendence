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
                type: message.type || 'chat_message',
                message: message.content || '',
                channel_name: `chat_${message.room}`,
                user_id: localStorage.getItem('user_id'),
                username: localStorage.getItem('username')
            };
            this.socket.send(JSON.stringify(formattedMessage));
        } else {
            console.error('Socket is not connected.');
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
