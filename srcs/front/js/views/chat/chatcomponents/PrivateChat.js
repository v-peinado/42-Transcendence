import { webSocketService } from '../../../services/WebSocketService.js';
import { blockService } from '../../../services/BlockService.js';

export class PrivateChat {
    constructor(container) {
        this.container = container;
        this.activeChats = new Map(); // userId -> {channelName, username}
        this.messageHistory = new Map(); // channelName -> messages[]
        this.closedChats = new Set(this.loadClosedChats()); // Añadir esto
        this.loadSavedChats();
        this.initializePrivateTabs();

        document.addEventListener('block-status-changed', () => {
            this.handleBlockStatusChange();
        });
    }

    initializePrivateTabs() {
        // Crear contenedor de pestañas privadas
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'cw-private-tabs';
        
        // Insertar después del header pero antes del contenido
        const header = this.container.querySelector('.cw-header');
        header.parentNode.insertBefore(tabsContainer, header.nextSibling);
    }

    updatePrivateTabs() {
        const tabsContainer = this.container.querySelector('.cw-private-tabs');
        tabsContainer.innerHTML = '';

        // Añadir pestaña del chat general
        const generalTab = document.createElement('button');
        generalTab.className = `cw-private-tab ${!this.activePrivateChat ? 'active' : ''}`;
        generalTab.innerHTML = `
            <i class="fas fa-comments"></i>
            <span>General</span>
        `;
        generalTab.onclick = () => this.showGeneralChat();
        tabsContainer.appendChild(generalTab);

        // Añadir pestañas de chats privados
        this.activeChats.forEach((chat, userId) => {
            const tab = document.createElement('button');
            tab.className = `cw-private-tab ${this.activePrivateChat === userId ? 'active' : ''}`;
            tab.innerHTML = `
                <span>${chat.username}</span>
                <span class="cw-tab-close">
                    <i class="fas fa-times"></i>
                </span>
            `;

            // Manejar clic en la pestaña
            tab.onclick = (e) => {
                if (!e.target.closest('.cw-tab-close')) {
                    this.showChat(userId);
                }
            };

            // Manejar clic en el botón de cerrar
            tab.querySelector('.cw-tab-close').onclick = (e) => {
                e.stopPropagation();
                this.closeChat(userId);
            };

            tabsContainer.appendChild(tab);
        });
    }

    createPrivateChat(userId, username) {
        // Si estaba en la lista de cerrados, quitarlo
        if (this.closedChats.has(userId)) {
            this.closedChats.delete(userId);
            this.saveClosedChats();
        }

        // Verificar bloqueos antes de crear el chat
        if (blockService.isBlocked(userId)) {
            console.log('Chat bloqueado:', userId);
            return;
        }

        const currentUserId = parseInt(localStorage.getItem('user_id'));
        const channelName = `dm_${Math.min(currentUserId, userId)}_${Math.max(currentUserId, userId)}`;
        
        // Verificar si el chat ya existe en el DOM
        let chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        
        if (!chatContainer) {
            // Crear nuevo contenedor de chat solo si no existe
            chatContainer = document.createElement('div');
            chatContainer.className = 'cw-tab-pane';
            chatContainer.id = `private-chat-${userId}`;
            
            chatContainer.innerHTML = `
                <div class="cw-private-chat-header">
                    <span class="cw-username">${username}</span>
                    <button class="cw-close-chat" title="Cerrar chat">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="cw-messages"></div>
                <div class="cw-input-container">
                    <div class="cw-input-wrapper">
                        <input type="text" class="cw-input" placeholder="Escribe un mensaje...">
                        <button class="cw-send-btn">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            `;

            // Asegurarse de que el contenedor se añade al DOM
            const tabContent = this.container.querySelector('.cw-tab-content');
            if (tabContent) {
                tabContent.appendChild(chatContainer);
            } else {
                console.error('No se encontró el contenedor .cw-tab-content');
                return;
            }
            
            // Configurar listeners
            this.setupChatListeners(chatContainer, userId, channelName);
        }

        // Guardar referencia del chat activo si no existe
        if (!this.activeChats.has(userId)) {
            this.activeChats.set(userId, { channelName, username });
            
            // Suscribirse al canal
            webSocketService.send({
                type: 'subscribe_to_channel',
                channel_name: channelName
            });

            // Solicitar historial
            webSocketService.send({
                type: 'request_chat_history',
                channel_name: channelName
            });
        }

        // Mostrar el chat
        this.showChat(userId);
        this.notifyServerNewChat(userId);
        
        // Guardar estado y actualizar pestañas
        this.saveChatsState();
        this.updatePrivateTabs();
    }

    showChat(userId) {
        console.log('Mostrando chat:', userId);
        
        // Ocultar todos los chats y el chat general
        this.container.querySelectorAll('.cw-tab-pane').forEach(pane => {
            pane.classList.remove('cw-active');
            pane.style.display = 'none';
        });
        
        // Mostrar el chat privado
        const chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        if (chatContainer) {
            chatContainer.classList.add('cw-active');
            chatContainer.style.display = 'flex';
            this.loadChatHistory(userId);
            chatContainer.querySelector('.cw-input')?.focus();
            
            this.activePrivateChat = userId;
            this.updatePrivateTabs();
        } else {
            console.error('No se encontró el contenedor del chat:', userId);
        }
    }

    showGeneralChat() {
        // Restaurar el estado original del widget
        this.container.querySelectorAll('.cw-tab-pane').forEach(pane => {
            // Primero quitamos la clase active de todos
            pane.classList.remove('cw-active');
            
            // Si es un chat privado, lo ocultamos
            if (pane.id.startsWith('private-chat-')) {
                pane.style.display = 'none';
            } else {
                // Para los paneles principales (chat, users, friends, requests)
                // restauramos su visibilidad normal
                pane.style.removeProperty('display');
            }
        });

        // Mostrar el chat general y activar su botón
        const chatTab = this.container.querySelector('#chat-tab');
        const chatBtn = this.container.querySelector('[data-tab="chat"]');
        
        if (chatTab && chatBtn) {
            chatTab.classList.add('cw-active');
            chatBtn.classList.add('cw-active');
        }

        // Asegurarnos de que los botones del header funcionen
        this.container.querySelectorAll('.cw-tab-btn').forEach(btn => {
            const originalClickListener = btn.onclick;
            btn.onclick = originalClickListener;
        });
        
        this.activePrivateChat = null;
        this.updatePrivateTabs();
    }

    setupChatListeners(chatContainer, userId, channelName) {
        const input = chatContainer.querySelector('.cw-input');
        const sendBtn = chatContainer.querySelector('.cw-send-btn');
        const closeBtn = chatContainer.querySelector('.cw-close-chat');

        const sendMessage = () => {
            const content = input.value.trim();
            if (!content) return;

            const messageData = {
                type: 'chat_message',
                content,
                channel_name: channelName,
                user_id: parseInt(localStorage.getItem('user_id')),
                username: localStorage.getItem('username')
            };

            webSocketService.send(messageData);
            
            // Añadir mensaje al historial
            this.addMessageToHistory(channelName, messageData);
            input.value = '';
        };

        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        closeBtn.addEventListener('click', () => this.closeChat(userId));
    }

    handlePrivateMessage(data) {
        const { channel_name, message, user_id, username } = data;
        
        // Extraer IDs del nombre del canal
        const [_, id1, id2] = channel_name.match(/dm_(\d+)_(\d+)/);
        const otherUserId = parseInt(id1) === parseInt(localStorage.getItem('user_id')) ? 
            parseInt(id2) : parseInt(id1);

        // No procesar mensajes si el usuario está bloqueado
        if (blockService.isBlocked(otherUserId)) {
            console.log('Mensaje de usuario bloqueado ignorado:', otherUserId);
            return;
        }

        // Guardar mensaje en el historial sin importar si el chat está abierto o no
        this.addMessageToHistory(channel_name, {
            content: message,
            user_id: parseInt(user_id),
            username,
            timestamp: new Date().toISOString()
        });

        // Si el chat está abierto, mostrar el mensaje
        if (this.activeChats.has(otherUserId)) {
            this.addMessageToChat(otherUserId, {
                content: message,
                user_id: parseInt(user_id),
                username
            });
        }

        // Emitir evento de notificación si el chat no está activo
        if (!this.container.querySelector(`#private-chat-${otherUserId}`)?.classList.contains('cw-active')) {
            const event = new CustomEvent('new-private-message', {
                detail: { userId: otherUserId, username, message }
            });
            document.dispatchEvent(event);
        }
    }

    createPrivateChatSilent(userId, username) {
        const currentUserId = parseInt(localStorage.getItem('user_id'));
        const channelName = `dm_${Math.min(currentUserId, userId)}_${Math.max(currentUserId, userId)}`;
        
        // Crear y ocultar el chat
        const chatContainer = document.createElement('div');
        chatContainer.className = 'cw-tab-pane';
        chatContainer.id = `private-chat-${userId}`;
        chatContainer.style.display = 'none';  // Ocultar el chat
        
        chatContainer.innerHTML = `
            <div class="cw-private-chat-header">
                <span class="cw-username">${username}</span>
                <button class="cw-close-chat" title="Cerrar chat">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="cw-messages"></div>
            <div class="cw-input-container">
                <div class="cw-input-wrapper">
                    <input type="text" class="cw-input" placeholder="Escribe un mensaje...">
                    <button class="cw-send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;

        // Añadir al DOM pero mantenerlo oculto
        this.container.querySelector('.cw-tab-content').appendChild(chatContainer);
        
        // Guardar referencia
        this.activeChats.set(userId, { channelName, username });
        
        // Configurar listeners pero mantener oculto
        this.setupChatListeners(chatContainer, userId, channelName);
        
        // Suscribirse al canal
        webSocketService.send({
            type: 'subscribe_to_channel',
            channel_name: channelName
        });
        
        this.saveChatsState();
        this.updatePrivateTabs();
    }

    addMessageToChat(userId, message) {
        console.log('Añadiendo mensaje a chat:', userId, message);
        const chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        if (!chatContainer) {
            console.error('No se encontró el contenedor del chat:', userId);
            return;
        }

        const messagesContainer = chatContainer.querySelector('.cw-messages');
        const messageElement = document.createElement('div');
        const isOwnMessage = message.user_id === parseInt(localStorage.getItem('user_id'));
        
        messageElement.className = `cw-message ${isOwnMessage ? 'cw-message-my' : 'cw-message-other'}`;
        messageElement.innerHTML = `
            <span class="cw-message-username">${message.username}</span>
            ${message.content || message.message}
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    closeChat(userId) {
        console.log('Cerrando chat:', userId);
        
        // Notificar al servidor
        const chatData = this.activeChats.get(userId);
        if (chatData) {
            webSocketService.send({
                type: 'delete_private_channel',
                user1_id: Math.min(parseInt(localStorage.getItem('user_id')), userId),
                user2_id: Math.max(parseInt(localStorage.getItem('user_id')), userId),
                deleting_user_id: parseInt(localStorage.getItem('user_id')),
                name: chatData.channelName
            });
        }

        // Eliminar el contenedor físicamente
        const chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        if (chatContainer) {
            chatContainer.remove();
        }

        // Eliminar todas las referencias
        this.activeChats.delete(userId);
        this.closedChats.add(userId);
        
        // Siempre volver al chat general al cerrar
        this.showGeneralChat();
        
        // Actualizar estado
        this.saveClosedChats();
        this.saveChatsState();
    }

    // Métodos para persistencia
    loadSavedChats() {
        try {
            const savedChats = JSON.parse(localStorage.getItem('activeChats') || '[]');
            const savedHistory = JSON.parse(localStorage.getItem('chatHistory') || '{}');
            const closedChats = new Set(JSON.parse(localStorage.getItem('closedChats') || '[]'));
            
            this.messageHistory = new Map(Object.entries(savedHistory));
            this.closedChats = closedChats;
            
            // Limpiar cualquier chat existente primero
            this.container.querySelectorAll('.cw-tab-pane[id^="private-chat-"]').forEach(el => el.remove());
            this.activeChats.clear();
            
            // Solo recrear los chats que no están cerrados
            savedChats.forEach(chat => {
                if (!this.closedChats.has(chat.userId)) {
                    this.createPrivateChatSilent(chat.userId, chat.username);
                }
            });
        } catch (error) {
            console.error('Error loading saved chats:', error);
        }
    }

    saveChatsState() {
        const chatsToSave = Array.from(this.activeChats.entries()).map(([userId, data]) => ({
            userId,
            username: data.username,
            channelName: data.channelName
        }));
        
        const historyToSave = Object.fromEntries(this.messageHistory);
        
        localStorage.setItem('activeChats', JSON.stringify(chatsToSave));
        localStorage.setItem('chatHistory', JSON.stringify(historyToSave));
    }

    addMessageToHistory(channelName, message) {
        if (!this.messageHistory.has(channelName)) {
            this.messageHistory.set(channelName, []);
        }
        this.messageHistory.get(channelName).push(message);
        this.saveChatsState();
    }

    loadChatHistory(userId) {
        const chatData = this.activeChats.get(userId);
        if (!chatData) return;

        const history = this.messageHistory.get(chatData.channelName) || [];
        const chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        
        if (chatContainer) {
            const messagesContainer = chatContainer.querySelector('.cw-messages');
            messagesContainer.innerHTML = '';
            history.forEach(msg => this.addMessageToChat(userId, msg));
        }
    }

    notifyServerNewChat(userId) {
        const currentUserId = parseInt(localStorage.getItem('user_id'));
        webSocketService.send({
            type: 'create_private_channel',
            user1_id: Math.min(currentUserId, userId),
            user2_id: Math.max(currentUserId, userId)
        });
    }

    loadClosedChats() {
        try {
            return new Set(JSON.parse(localStorage.getItem('closedChats') || '[]'));
        } catch (error) {
            console.error('Error loading closed chats:', error);
            return new Set();
        }
    }

    saveClosedChats() {
        localStorage.setItem('closedChats', JSON.stringify([...this.closedChats]));
    }

    // Método para reabrir un chat cerrado
    reopenChat(userId, username) {
        this.closedChats.delete(userId);
        this.saveClosedChats();
        this.createPrivateChat(userId, username);
    }

    // Método para manejar la lista de canales privados (similar a chat.html)
    handlePrivateChannelList(channels) {
        console.log('Recibiendo lista de canales privados:', channels);
        
        // Limpiar chats que ya no existen en el servidor
        const activeChannelIds = new Set(channels.map(channel => {
            const otherUser = channel.members.find(m => 
                m.id !== parseInt(localStorage.getItem('user_id'))
            );
            return otherUser?.id;
        }));

        // Eliminar chats que ya no existen en el servidor
        Array.from(this.activeChats.keys()).forEach(userId => {
            if (!activeChannelIds.has(userId)) {
                const chatContainer = this.container.querySelector(`#private-chat-${userId}`);
                if (chatContainer) {
                    chatContainer.remove();
                }
                this.activeChats.delete(userId);
            }
        });

        // Actualizar o crear nuevos chats
        channels.forEach(channel => {
            const otherUser = channel.members.find(m => 
                m.id !== parseInt(localStorage.getItem('user_id'))
            );
            if (otherUser) {
                // Solo guardar la referencia, no crear la UI todavía
                this.activeChats.set(otherUser.id, {
                    channelName: channel.name,
                    username: otherUser.username
                });
            }
        });

        this.updatePrivateTabs();
        this.saveChatsState();
    }

    handleBlockStatusChange() {
        // Cerrar chats de usuarios bloqueados
        Array.from(this.activeChats.keys()).forEach(userId => {
            if (blockService.isBlocked(userId)) {
                this.closeChat(userId);
            }
        });
    }

    // Sobreescribir createPrivateChat para que solo abra chats explícitamente
    createPrivateChat(userId, username) {
        const currentUserId = parseInt(localStorage.getItem('user_id'));
        const channelName = `dm_${Math.min(currentUserId, userId)}_${Math.max(currentUserId, userId)}`;
        
        // Si ya existe el chat en activeChats, solo abrirlo
        if (this.activeChats.has(userId)) {
            this.openExistingChat(userId);
            return;
        }

        // Si no existe, crear nuevo
        // Crear nuevo contenedor de chat
        const chatContainer = document.createElement('div');
        chatContainer.className = 'cw-tab-pane';
        chatContainer.id = `private-chat-${userId}`;
        
        chatContainer.innerHTML = `
            <div class="cw-private-chat-header">
                <span class="cw-username">${username}</span>
                <button class="cw-close-chat" title="Cerrar chat">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="cw-messages"></div>
            <div class="cw-input-container">
                <div class="cw-input-wrapper">
                    <input type="text" class="cw-input" placeholder="Escribe un mensaje...">
                    <button class="cw-send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;

        // Añadir el chat al DOM
        this.container.querySelector('.cw-tab-content').appendChild(chatContainer);
        
        // Guardar referencia del chat activo
        this.activeChats.set(userId, { channelName, username });
        
        // Configurar listeners
        this.setupChatListeners(chatContainer, userId, channelName);
        
        // Mostrar el chat y notificar al servidor
        this.showChat(userId);
        this.notifyServerNewChat(userId);
        
        // Suscribirse al canal después de crear el chat
        webSocketService.send({
            type: 'subscribe_to_channel',
            channel_name: channelName
        });

        // Solicitar historial inmediatamente
        webSocketService.send({
            type: 'request_chat_history',
            channel_name: channelName
        });

        // Mostrar el chat inmediatamente
        this.showChat(userId);
        
        // Guardar estado
        this.saveChatsState();
        this.updatePrivateTabs();
    }

    openExistingChat(userId) {
        const chatData = this.activeChats.get(userId);
        if (!chatData) return;

        // Crear la interfaz del chat si no existe
        if (!this.container.querySelector(`#private-chat-${userId}`)) {
            this.createChatInterface(userId, chatData.username, chatData.channelName);
        }

        // Mostrar el chat y cargar mensajes
        this.showChat(userId);
        this.loadChatHistory(userId);
    }
}