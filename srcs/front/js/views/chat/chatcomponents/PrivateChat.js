import { webSocketService } from '../../../services/WebSocketService.js';

export class PrivateChat {
    constructor(container) {
        this.container = container;
        this.chatTabs = container.querySelector('#chat-tabs');
        this.chatContainers = container.querySelector('#chat-containers');
        this.messageHistory = new Map();
        this.activeChats = new Map(); // Almacena los chats activos
        this.chatTabManager = null;
        this.currentPrivateChat = null; // Añadido para tracking del chat actual
        this.loadSavedChats();
    }

    setChatTabManager(manager) {
        this.chatTabManager = manager;
    }

    createPrivateChatTab(userId, username) {
        const tabId = `user-${userId}`;
        
        // Crear el botón del tab si no existe
        if (!this.chatTabs.querySelector(`[data-tab="${tabId}"]`)) {
            const tabButton = document.createElement('button');
            tabButton.className = 'btn btn-primary';
            tabButton.setAttribute('data-tab', tabId);
            tabButton.innerHTML = `
                <i class="fas fa-user me-2"></i>${username}
                <button class="btn-close ms-2" data-user-id="${userId}"></button>
            `;
            
            // Añadir el botón de cerrar
            const closeBtn = tabButton.querySelector('.btn-close');
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closePrivateChat(userId);
            });

            this.chatTabs.appendChild(tabButton);
        }

        // Crear el contenedor del chat si no existe
        if (!document.getElementById(`private-chat-${tabId}`)) {
            const chatContainer = document.createElement('div');
            chatContainer.id = `private-chat-${tabId}`;
            chatContainer.className = 'chat-column';
            chatContainer.innerHTML = `
                <div class="chat-header">
                    <h2 class="section-title">
                        <i class="fas fa-comments me-2"></i>
                        Chat con ${username}
                    </h2>
                </div>
                <div class="chat-log"></div>
                <div class="form-group mt-3">
                    <div class="input-group">
                        <input type="text" class="form-control private-message-input" 
                            placeholder="Escribe un mensaje..." autocomplete="off">
                        <button class="btn btn-primary private-send-button">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            `;
            
            this.chatContainers.appendChild(chatContainer);
            this.initializeChatListeners(chatContainer, userId);
        }

        return tabId;
    }

    showChat(channelName, username, userId) {
        if (!userId) {
            userId = this.getUserIdFromChannelName(channelName);
        }
        
        const tabId = this.createPrivateChatTab(userId, username);
        this.activeChats.set(userId, { channelName, username });
        this.currentPrivateChat = channelName;

        // Primero creamos y nos suscribimos al canal
        const myUserId = parseInt(localStorage.getItem('user_id'));
        
        webSocketService.send({
            type: 'create_private_channel',
            user1_id: Math.min(myUserId, userId),
            user2_id: Math.max(myUserId, userId)
        });

        // Guardar en localStorage
        this.saveActiveChats();
        
        // Activar el tab
        const tabButton = this.chatTabs.querySelector(`[data-tab="${tabId}"]`);
        if (tabButton) {
            tabButton.click();
        }

        // Mostrar el contenedor correcto
        document.getElementById('general-chat').classList.remove('active');
        const chatContainer = document.getElementById(`private-chat-${tabId}`);
        if (chatContainer) {
            chatContainer.classList.add('active');
        }
        
        // Cargar historial si existe
        const chatLog = document.querySelector(`#private-chat-${tabId} .chat-log`);
        const history = this.messageHistory.get(channelName) || [];
        if (chatLog) {
            chatLog.innerHTML = '';
            history.forEach(msg => this.addMessage(msg, tabId));
        }

        // Enfocar el input
        const input = document.querySelector(`#private-chat-${tabId} .private-message-input`);
        if (input) {
            input.focus();
        }
    }

    closePrivateChat(userId) {
        const tabId = `user-${userId}`;
        const tab = this.chatTabs.querySelector(`[data-tab="${tabId}"]`);
        const container = document.getElementById(`private-chat-${tabId}`);
        
        // Si este era el tab activo, cambiar al general
        if (tab.classList.contains('active')) {
            this.chatTabs.querySelector('[data-tab="general"]').click();
        }
        
        tab.remove();
        container.remove();
        this.activeChats.delete(userId);
        this.saveActiveChats();
    }

    addMessage(data, tabId) {
        // Si no se proporciona tabId, intentar obtenerlo del canal
        if (!tabId && data.channel_name) {
            const userId = this.getUserIdFromChannelName(data.channel_name);
            if (userId) {
                tabId = `user-${userId}`;
            }
        }

        const chatLog = document.querySelector(`#private-chat-${tabId} .chat-log`);
        if (!chatLog) return;

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('msg');
        messageDiv.classList.add(
            data.user_id === parseInt(localStorage.getItem('user_id')) 
                ? 'my-msg' 
                : 'other-msg'
        );
        
        messageDiv.innerHTML = `
            <small class="d-block mb-1 text-muted">${data.username}</small>
            <span>${data.message || data.content}</span>
        `;
        
        chatLog.appendChild(messageDiv);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    initializeChatListeners(chatContainer, userId) {
        const input = chatContainer.querySelector('.private-message-input');
        const sendButton = chatContainer.querySelector('.private-send-button');

        const sendMessage = () => {
            const content = input.value.trim();
            const channelInfo = this.activeChats.get(userId);

            if (content && channelInfo) {
                const message = {
                    type: 'chat_message',
                    message: content,
                    content: content,
                    channel_name: channelInfo.channelName,
                    user_id: parseInt(localStorage.getItem('user_id')),
                    username: localStorage.getItem('username')
                };

                console.log('Sending private message:', message);
                webSocketService.send(message);
                
                input.value = '';
                input.focus();
            }
        };

        sendButton.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    handleHistoricalMessage(data) {
        if (!data.channel_name?.startsWith('dm_')) return;
        
        const userId = this.getUserIdFromChannelName(data.channel_name);
        if (!userId) return;

        // Si el chat no está abierto, abrirlo
        if (!this.activeChats.has(userId)) {
            this.showChat(data.channel_name, data.username, userId);
            return;
        }

        // Almacenar en historial y mostrar el mensaje
        const tabId = `user-${userId}`;
        
        // Verificar si el mensaje ya existe en el historial para evitar duplicados
        const messages = this.messageHistory.get(data.channel_name) || [];
        const messageExists = messages.some(msg => 
            msg.message === data.message && 
            msg.user_id === data.user_id &&
            msg.timestamp === data.timestamp
        );

        if (!messageExists) {
            messages.push(data);
            this.messageHistory.set(data.channel_name, messages);
            this.addMessage(data, tabId);
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

    getUserIdFromChannelName(channelName) {
        if (!channelName?.startsWith('dm_')) return null;
        const [_, id1, id2] = channelName.split('_');
        const myUserId = parseInt(localStorage.getItem('user_id'));
        return parseInt(id1) === myUserId ? parseInt(id2) : parseInt(id1);
    }

    loadSavedChats() {
        try {
            const savedChats = JSON.parse(localStorage.getItem('activeChats') || '[]');
            savedChats.forEach(chat => {
                this.showChat(chat.channelName, chat.username, chat.userId);
            });
        } catch (error) {
            console.error('Error loading saved chats:', error);
        }
    }

    saveActiveChats() {
        const chatsToSave = Array.from(this.activeChats.entries()).map(([userId, chat]) => ({
            userId,
            channelName: chat.channelName,
            username: chat.username
        }));
        localStorage.setItem('activeChats', JSON.stringify(chatsToSave));
    }
}