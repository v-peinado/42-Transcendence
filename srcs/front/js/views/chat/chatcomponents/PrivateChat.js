import { webSocketService } from '../../../services/WebSocketService.js';

export class PrivateChat {
    constructor(container) {
        // Referencias DOM
        this.container = container;
        this.privateChatsContainer = container.querySelector('.private-chats-list');
        this.privateChatUsername = container.querySelector('#private-chat-username');
        this.privateMessages = container.querySelector('#private-messages');
        this.privateMessageInput = container.querySelector('#private-message-input');
        this.privateSendButton = container.querySelector('#private-send-button');
        
        // Estado
        this.currentPrivateChat = null;
        this.messageHistory = new Map();
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Enviar mensaje con botón
        this.privateSendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Enviar mensaje con Enter
        this.privateMessageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    sendMessage() {
        const content = this.privateMessageInput.value.trim();
        if (content && this.currentPrivateChat) {
            webSocketService.send({
                type: 'chat_message',
                content: content,
                channel_name: this.currentPrivateChat
            });
            this.privateMessageInput.value = '';
        }
    }

    showChat(channelName, username) {
        this.currentPrivateChat = channelName;
        
        // Actualizar interfaz
        this.privateChatUsername.textContent = username;
        this.privateMessages.innerHTML = '';
        
        // Mostrar mensajes históricos
        const history = this.messageHistory.get(channelName) || [];
        history.forEach(msg => this.addMessage(msg));
        
        this.privateMessages.scrollTop = this.privateMessages.scrollHeight;
        this.privateMessageInput.value = '';
        
        // Asegurar que el contenedor esté visible
        const privateChatsColumn = document.getElementById('private-chats');
        privateChatsColumn.classList.add('active');
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
        
        this.privateMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    handleHistoricalMessage(data) {
        if (!data.channel_name?.startsWith('dm_')) return;
        
        // Almacenar en historial
        if (!this.messageHistory.has(data.channel_name)) {
            this.messageHistory.set(data.channel_name, []);
        }
        
        const messages = this.messageHistory.get(data.channel_name);
        const timestamp = new Date(data.timestamp);
        messages.push({...data, timestamp});
        messages.sort((a, b) => a.timestamp - b.timestamp);

        // Si es el chat actual, mostrar el mensaje
        if (data.channel_name === this.currentPrivateChat) {
            this.addMessage(data);
        } else {
            this.showNotification(data);
        }
    }

    showNotification(data) {
        if (data.user_id === parseInt(localStorage.getItem('user_id'))) return;

        const userItem = document.querySelector(`.user-item[data-user-id="${data.user_id}"]`);
        if (userItem && !userItem.querySelector('.notification-dot')) {
            const dot = document.createElement('span');
            dot.className = 'notification-dot';
            userItem.appendChild(dot);
        }
    }

    updateChannelsList(data) {
        this.privateChatsContainer.innerHTML = '';
        
        data.channels.forEach(channel => {
            const otherUser = channel.members.find(
                m => m.id !== parseInt(localStorage.getItem('user_id'))
            );
            
            if (otherUser) {
                const chatDiv = document.createElement('div');
                chatDiv.className = 'list-group-item private-chat-item';
                chatDiv.innerHTML = `
                    <i class="fas fa-user me-2"></i>
                    ${otherUser.username}
                `;
                
                chatDiv.addEventListener('click', () => 
                    this.showChat(channel.name, otherUser.username)
                );
                
                this.privateChatsContainer.appendChild(chatDiv);
            }
        });
    }

    scrollToBottom() {
        this.privateMessages.scrollTop = this.privateMessages.scrollHeight;
    }

    clearCurrentChat() {
        this.currentPrivateChat = null;
        this.privateMessages.innerHTML = '';
        this.privateChatUsername.textContent = '';
    }
}
