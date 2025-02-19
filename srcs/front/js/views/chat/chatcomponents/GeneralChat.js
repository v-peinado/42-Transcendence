import { webSocketService } from '../../../services/WebSocketService.js';

export class GeneralChat {
    constructor(container) {
        // Referencias DOM
        this.container = container;
        this.messagesContainer = container.querySelector('#messages');
        this.messageInput = container.querySelector('#message-input');
        this.sendButton = container.querySelector('#send-button');
        
        // Inicializar
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Evento para enviar mensaje con botón
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Evento para enviar mensaje con Enter
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Si no es pantalla completa, manejar colapso
        if (window.location.pathname !== '/chat') {
            this.initializeCollapseFeature();
        }
    }

    sendMessage() {
        const content = this.messageInput.value.trim();
        if (content) {
            webSocketService.send({
                type: 'chat_message',
                content: content,
                room: 'general'
            });
            this.messageInput.value = '';
        }
    }

    addMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('msg');
        messageDiv.classList.add(
            data.user_id === parseInt(localStorage.getItem('user_id')) 
                ? 'my-msg' 
                : 'other-msg'
        );
        
        messageDiv.innerHTML = `
            <small class="d-block mb-1 text-muted">${data.username}</small>
            <span>${data.message}</span>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    initializeCollapseFeature() {
        const chatHeader = this.container.querySelector('#chatHeader');
        if (chatHeader) {
            chatHeader.addEventListener('click', () => {
                this.container.classList.toggle('collapsed');
                localStorage.setItem(
                    'chatCollapsed', 
                    this.container.classList.contains('collapsed')
                );
            });

            // Restaurar estado anterior
            const wasCollapsed = localStorage.getItem('chatCollapsed') === 'true';
            if (wasCollapsed) {
                this.container.classList.add('collapsed');
            }
        }
    }

    // Método para limpiar el chat
    clear() {
        this.messagesContainer.innerHTML = '';
    }
}