class ChatService {
    constructor() {
        this.socket = null;
        this.messageCallbacks = new Map();
        this.roomName = 'general';
        this.username = localStorage.getItem('username');
        this.userId = localStorage.getItem('user_id');
    }

    init(websocketService) {
        this.socket = websocketService;
        this.setupMessageHandlers();
    }

    setupMessageHandlers() {
        // Escuchar mensajes de chat
        this.socket.on('chat_message', (data) => {
            if (this.messageCallbacks.has('onMessage')) {
                this.messageCallbacks.get('onMessage')(data);
            }
        });

        // Escuchar actualizaciones de lista de usuarios
        this.socket.on('user_list', (data) => {
            if (this.messageCallbacks.has('onUserList')) {
                this.messageCallbacks.get('onUserList')(data);
            }
        });
    }

    onMessage(callback) {
        this.messageCallbacks.set('onMessage', callback);
    }

    onUserList(callback) {
        this.messageCallbacks.set('onUserList', callback);
    }

    sendMessage(content, room = 'general') {
        this.socket.send({
            type: 'chat_message',
            content,
            room
        });
    }
}

export const chatService = new ChatService();
