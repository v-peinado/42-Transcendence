import { webSocketService } from '../services/WebSocketService.js';

export class ChatWidget {
    static instance = null;
    
    constructor() {
        if (ChatWidget.instance) {
            return ChatWidget.instance;
        }
        ChatWidget.instance = this;
        
        this.container = null;
        this.isMinimized = true;
        this.unreadCount = 0;
    }

    static async initialize() {
        const widget = new ChatWidget();
        if (!widget.container && !window.location.pathname.includes('/chat')) {
            await widget.mount();
        }
        return widget;
    }

    async mount() {
        // Crear el contenedor del widget
        this.container = document.createElement('div');
        this.container.className = 'chat-widget-container';
        
        // Crear la estructura completa del widget
        this.container.innerHTML = `
            <div class="chat-widget">
                <div class="chat-widget-content">
                    <div class="chat-widget-header">
                        <h3><i class="fas fa-comments"></i> Chat General</h3>
                        <div class="chat-controls">
                            <button class="minimize-btn">
                                <i class="fas fa-minus"></i>
                            </button>
                        </div>
                    </div>
                    <div id="widget-messages" class="chat-log"></div>
                    <div class="input-group">
                        <input type="text" id="widget-message-input" class="form-control" 
                            placeholder="Escribe un mensaje..." autocomplete="off">
                        <button type="submit" id="widget-send-button" class="btn btn-primary">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
            <button class="chat-toggle-btn">
                <i class="fas fa-comments"></i>
            </button>
        `;

        // Obtener referencias a elementos
        const toggleBtn = this.container.querySelector('.chat-toggle-btn');
        const chatWidget = this.container.querySelector('.chat-widget');
        const minimizeBtn = this.container.querySelector('.minimize-btn');
        const messageInput = this.container.querySelector('#widget-message-input');
        const sendButton = this.container.querySelector('#widget-send-button');
        const messagesContainer = this.container.querySelector('#widget-messages');

        // Configurar eventos
        toggleBtn.addEventListener('click', () => {
            this.isMinimized = !this.isMinimized;
            chatWidget.classList.toggle('visible');
            toggleBtn.querySelector('i').classList.toggle('fa-comments');
            toggleBtn.querySelector('i').classList.toggle('fa-times');
        });

        // Configurar evento de minimizar
        minimizeBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Evitar que el click se propague
            chatWidget.classList.remove('visible');
            toggleBtn.querySelector('i').classList.remove('fa-times');
            toggleBtn.querySelector('i').classList.add('fa-comments');
            this.isMinimized = true;
        });

        // Manejar envío de mensajes - Actualizamos el formato
        const sendMessage = () => {
            const messageInput = this.container.querySelector('#widget-message-input');
            const message = messageInput.value.trim();
            if (message) {
                const messageData = {
                    type: 'chat_message',
                    content: message,
                    room: 'general',
                    channel_name: 'chat_general',  // Añadimos esto para consistencia
                    user_id: parseInt(localStorage.getItem('user_id')),
                    username: localStorage.getItem('username')
                };
                
                console.log('Enviando mensaje:', messageData);
                webSocketService.send(messageData);
                messageInput.value = '';
            }
        };

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Escuchar mensajes nuevos - Actualizamos esta parte
        webSocketService.on('chat_message', (data) => {
            console.log('Mensaje recibido en widget:', data);
            const messageContent = data.message || data.content; // Manejar ambos formatos
            if (!messageContent) return;
            
            const messageElement = document.createElement('div');
            messageElement.className = `msg ${
                data.user_id === parseInt(localStorage.getItem('user_id')) 
                    ? 'my-msg' 
                    : 'other-msg'
            }`;
            
            messageElement.innerHTML = `
                <small>${data.username}</small>
                ${messageContent}
            `;
            
            const messagesContainer = this.container.querySelector('#widget-messages');
            if (messagesContainer) {
                messagesContainer.appendChild(messageElement);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                console.log('Mensaje añadido al contenedor');
            } else {
                console.error('No se encontró el contenedor de mensajes');
            }

            if (this.isMinimized) {
                this.incrementUnreadCount();
            }
        });

        // Asegurarnos de que el WebSocket esté conectado antes de empezar
        if (!webSocketService.socket || webSocketService.socket.readyState !== WebSocket.OPEN) {
            await webSocketService.connect('general');
        }

        document.body.appendChild(this.container);
    }

    incrementUnreadCount() {
        this.unreadCount++;
        this.updateNotificationBadge();
    }

    resetUnreadCount() {
        this.unreadCount = 0;
        this.updateNotificationBadge();
    }

    updateNotificationBadge() {
        const toggleBtn = this.container.querySelector('.chat-toggle-btn');
        let badge = toggleBtn.querySelector('.chat-notification');
        
        if (this.unreadCount > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'chat-notification';
                toggleBtn.appendChild(badge);
            }
            badge.textContent = this.unreadCount > 9 ? '9+' : this.unreadCount;
        } else if (badge) {
            badge.remove();
        }
    }
}
