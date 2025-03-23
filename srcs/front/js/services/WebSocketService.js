class WebSocketService {
    constructor() {
        this.socket = null;
        this.listeners = new Map();
        this.keepAliveInterval = null;
        this.messageQueue = [];
        this.isConnecting = false;
    }

    async connect(roomName = 'general') {
        if (this.isConnecting) return;
        this.isConnecting = true;

        return new Promise((resolve, reject) => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const wsUrl = `${protocol}//${host}/ws/chat/${roomName}/`;

            try {
                // Añadir opciones para el WebSocket
                const options = {
                    rejectUnauthorized: false
                };

                this.socket = new WebSocket(wsUrl);
                
                this.socket.addEventListener('error', (error) => {
                    console.error('WebSocket SSL Error:', error);
                    // Intentar reconectar con un retraso
                    setTimeout(() => {
                        if (!this.socket || this.socket.readyState === WebSocket.CLOSED) {
                            console.log('Intentando reconectar...');
                            this.connect(roomName);
                        }
                    }, 3000);
                });

                this.socket.onopen = () => {
                    this.isConnecting = false;
                    
                    // Solicitar lista de usuarios online al conectar
                    this.send({
                        type: 'request_online_users'
                    });

                    // Procesar mensajes en cola
                    while (this.messageQueue.length > 0) {
                        const message = this.messageQueue.shift();
                        this.send(message);
                    }
                    resolve(this.socket);
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
                    reject(error);
                };
            } catch (error) {
                console.error('Error al crear WebSocket:', error);
                this.isConnecting = false;
                reject(error);
            }
        });
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
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            this.messageQueue.push(message);
            if (!this.isConnecting) {
                this.connect();
            }
            return;
        }

        let formattedMessage = {};

        switch (message.type) {
            case 'send_friend_request':
                formattedMessage = {
                    type: 'send_friend_request',
                    from_user_id: parseInt(localStorage.getItem('user_id')),
                    to_user_id: parseInt(message.to_user_id)
                };
                break;
            case 'chat_message':
                formattedMessage = {
                    type: message.type,
                    message: message.content || '',
                    channel_name: message.channel_name || `chat_${message.room}`,
                    user_id: parseInt(localStorage.getItem('user_id')),
                    username: localStorage.getItem('username')
                };
                break;
            default:
                formattedMessage = { ...message };
        }
        
        this.socket.send(JSON.stringify(formattedMessage));
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
                if (callbacks.length === 0) {
                    this.listeners.delete(eventType);
                }
            }
        }
    }
}

export const webSocketService = new WebSocketService();