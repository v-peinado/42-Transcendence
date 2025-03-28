import { webSocketService } from '../../../services/WebSocketService.js';
import { blockService } from '../../../services/BlockService.js';
import { soundService } from '../../../services/SoundService.js';

export class PrivateChat {
    constructor(container) {
        this.container = container;
        this.activeChats = new Map(); // userId -> {channelName, username}
        this.messageHistory = new Map(); // channelName -> messages[]
        this.closedChats = new Set(this.loadClosedChats()); // Añadir esto
        
        // Primero inicializar la interfaz
        this.initializePrivateTabs();
        this.setupMainTabsListeners();
        
        // Después cargar los datos
        this.loadSavedChats();
        
        this.pendingChallenges = new Set();

        document.addEventListener('block-status-changed', () => {
            this.handleBlockStatusChange();
        });

        // Agregar listener para challenge_action
        webSocketService.on('challenge_action', (data) => {
            this.handleChallengeAction(data);
        });

        // Agregar métodos para gestionar las respuestas de invitación
        window.acceptChallenge = (fromUserId, fromUsername, channelName) => {
            webSocketService.send({
                type: 'challenge_action',
                action: 'accept',
                from_user_id: fromUserId,
                to_username: localStorage.getItem('username'),
                channel_name: channelName
            });
        };

        window.rejectChallenge = (fromUserId, fromUsername, channelName) => {
            webSocketService.send({
                type: 'challenge_action',
                action: 'reject',
                from_user_id: fromUserId,
                to_username: localStorage.getItem('username'),
                channel_name: channelName
            });
        };
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
            return;
        }

        const currentUserId = parseInt(localStorage.getItem('user_id'));
        const channelName = `dm_${Math.min(currentUserId, userId)}_${Math.max(currentUserId, userId)}`;
        
        // Verificar si el chat ya existe en el DOM
        let chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        
        if (!chatContainer) {
            // Crear nuevo contenedor de chat solo si no existe
            chatContainer = this.createChatInterface(userId, username, channelName);
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
        
        // Mostrar el chat privado seleccionado
        const chatContainer = this.container.querySelector(`#private-chat-${userId}`);
        if (chatContainer) {
            // Ocultar todos los paneles primero
            this.container.querySelectorAll('.cw-tab-pane').forEach(pane => {
                pane.classList.remove('cw-active');
                pane.style.display = 'none';
            });
            
            chatContainer.classList.add('cw-active');
            chatContainer.style.display = 'flex';
            this.loadChatHistory(userId);
            chatContainer.querySelector('.cw-input')?.focus();
                        
            this.activePrivateChat = userId;
            this.updatePrivateTabs();

            // Mantener activos los listeners de las pestañas principales
            this.setupMainTabsListeners();
        } else {
            console.error('No se encontró el contenedor del chat:', userId);
        }
    }

    showGeneralChat() {
        // Restaurar el estado original del widget
        this.container.querySelectorAll('.cw-tab-pane').forEach(pane => {
            pane.classList.remove('cw-active');
            pane.style.display = 'none';
        });

        // Mostrar el chat general y activar su botón
        const chatTab = this.container.querySelector('#chat-tab');
        const chatBtn = this.container.querySelector('[data-tab="chat"]');
           
        if (chatTab && chatBtn) {
            chatTab.classList.add('cw-active');
            chatBtn.classList.add('cw-active');
            chatTab.style.display = 'flex';
        }
        
        this.activePrivateChat = null;
        this.updatePrivateTabs();
        this.enableMainTabs();
    }

    enableMainTabs() {
        this.container.querySelectorAll('.cw-tab-btn').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                
                // Desactivar todos los paneles y botones
                this.container.querySelectorAll('.cw-tab-pane').forEach(pane => {
                    pane.classList.remove('cw-active');
                    pane.style.display = 'none';
                });
                
                this.container.querySelectorAll('.cw-tab-btn').forEach(b => 
                    b.classList.remove('cw-active')
                );
                
                // Activar el panel y botón seleccionados
                const tabId = `${btn.getAttribute('data-tab')}-tab`;
                const targetPane = this.container.querySelector(`#${tabId}`);
                if (targetPane) {
                    targetPane.classList.add('cw-active');
                    targetPane.style.display = 'flex';
                }
                btn.classList.add('cw-active');
                     
                // Asegurarse de que los chats privados estén ocultos
                this.container.querySelectorAll('.cw-tab-pane[id^="private-chat-"]').forEach(pane => {
                    pane.style.display = 'none';
                });
                
                // Reset del estado del chat privado activo
                this.activePrivateChat = null;
                this.updatePrivateTabs();
            };
        });
    }

    setupMainTabsListeners() {
        // Configurar los listeners de las pestañas principales
        this.container.querySelectorAll('.cw-tab-btn').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                
                // Ocultar todos los paneles
                this.container.querySelectorAll('.cw-tab-pane').forEach(pane => {
                    pane.classList.remove('cw-active');
                    pane.style.display = 'none';
                });
                
                // Desactivar todos los botones
                this.container.querySelectorAll('.cw-tab-btn').forEach(b => 
                    b.classList.remove('cw-active')
                );
                
                // Activar el panel y botón seleccionados
                const tabId = `${btn.getAttribute('data-tab')}-tab`;
                const targetPane = this.container.querySelector(`#${tabId}`);
                if (targetPane) {
                    targetPane.classList.add('cw-active');
                    targetPane.style.display = 'flex';
                }
                btn.classList.add('cw-active');
                
                // Ocultar el chat privado si está activo
                if (this.activePrivateChat) {
                    const activeChat = this.container.querySelector(`#private-chat-${this.activePrivateChat}`);
                    if (activeChat) {
                        activeChat.style.display = 'none';
                        activeChat.classList.remove('cw-active');
                    }
                }
                
                // No resetear el estado del chat privado activo
                // Solo actualizar las pestañas
                this.updatePrivateTabs();
            };
        });
    }

    setupChatListeners(chatContainer, userId, channelName) {
        const input = chatContainer.querySelector('.cw-input');
        const sendBtn = chatContainer.querySelector('.cw-send-btn');
        const closeBtn = chatContainer.querySelector('.cw-close-chat');
        const emojiBtn = chatContainer.querySelector('.cw-emoji-btn');
        const emojiPicker = chatContainer.querySelector('.cw-emoji-picker');

        // Configurar emoji picker
        if (emojiBtn && emojiPicker) {
            emojiBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                emojiPicker.classList.toggle('visible');
            });

            emojiPicker.addEventListener('click', (e) => {
                if (e.target.classList.contains('cw-emoji-item')) {
                    const emoji = e.target.dataset.emoji;
                    const start = input.selectionStart;
                    const end = input.selectionEnd;
                    input.value = input.value.slice(0, start) + emoji + input.value.slice(end);
                    input.focus();
                    input.selectionStart = input.selectionEnd = start + emoji.length;
                    emojiPicker.classList.remove('visible');
                }
                e.stopPropagation();
            });

            // Cerrar el picker al hacer click fuera
            document.addEventListener('click', () => {
                emojiPicker.classList.remove('visible');
            });
        }

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
        const otherUserId = parseInt(id1) === parseInt(localStorage.getItem('user_id')) ? parseInt(id2) : parseInt(id1);

        // No procesar mensajes si el usuario está bloqueado
        if (blockService.isBlocked(otherUserId)) {
            return;
        }

        // Crear un ID único para el mensaje basado en su contenido y timestamp
        const messageId = `${channel_name}-${data.timestamp || Date.now()}-${message || data.content}`;

        // Verificar si el mensaje ya ha sido procesado
        if (this.processedMessages?.has(messageId)) {
            return;
        }

        // Marcar el mensaje como procesado
        if (!this.processedMessages) {
            this.processedMessages = new Set();
        }
        this.processedMessages.add(messageId);

        // Guardar mensaje en el historial
        this.addMessageToHistory(channel_name, {
            content: message || data.content,
            user_id: parseInt(user_id),
            username,
            timestamp: data.timestamp || new Date().toISOString(),
            messageId
        });

        // Si el chat está abierto, mostrar el mensaje
        if (this.activeChats.has(otherUserId)) {
            this.addMessageToChat(otherUserId, {
                content: message || data.content,
                user_id: parseInt(user_id),
                username,
                messageId
            });
        }

        // Emitir evento de notificación si el chat no está activo
        if (!this.container.querySelector(`#private-chat-${otherUserId}`)?.classList.contains('cw-active')) {
            const event = new CustomEvent('new-private-message', {
                detail: { otherUserId, username, message: message || data.content }
            });
            document.dispatchEvent(event);
        }
    }

    addMessageToChat(userId, message) {
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

            // Filtrar mensajes de usuarios bloqueados antes de cargar el historial
            const filteredHistory = {};
            for (const [channelName, messages] of Object.entries(savedHistory)) {
                filteredHistory[channelName] = messages.filter(msg => 
                    !blockService.isBlocked(parseInt(msg.user_id))
                );
            }
            
            this.messageHistory = new Map(Object.entries(filteredHistory));
            this.closedChats = closedChats;
            
            // Limpiar cualquier chat existente primero
            this.container.querySelectorAll('.cw-tab-pane[id^="private-chat-"]').forEach(el => el.remove());
            this.activeChats.clear();
            this.showGeneralChat();
            // Solo recrear los chats que no están cerrados
            savedChats.forEach(chat => {
                if (!this.closedChats.has(chat.userId) && !blockService.isBlocked(chat.userId)) {
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
        // Solo añadir al historial si el usuario no está bloqueado
        const messageUserId = parseInt(message.user_id);
        if (blockService.isBlocked(messageUserId)) {
            return;
        }

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

            // Filtrar mensajes duplicados usando messageId
            const processedIds = new Set();
            const uniqueMessages = history.filter(msg => {
                if (!msg.messageId || processedIds.has(msg.messageId)) {
                    return false;
                }
                processedIds.add(msg.messageId);
                return !blockService.isBlocked(parseInt(msg.user_id));
            });

            uniqueMessages.forEach(msg => this.addMessageToChat(userId, msg));
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
        const chatContainer = this.createChatInterface(userId, username, channelName);

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

        // Solicitar historial inmediatamente
        webSocketService.send({
            type: 'request_chat_history',
            channel_name: chatData.channelName
        });

        // Guardar estado
        this.saveChatsState();
        this.updatePrivateTabs();
    }

    createChatInterface(userId, username, channelName) {
        const chatContainer = document.createElement('div');
        chatContainer.className = 'cw-tab-pane';
        chatContainer.id = `private-chat-${userId}`;
        
        chatContainer.innerHTML = `
            <div class="cw-private-chat-header">
                <span class="cw-username">${username}</span>
                <div class="cw-header-actions">
                    <button class="cw-game-invite-btn" title="Invitar a jugar">
                        <i class="fas fa-gamepad"></i>
                    </button>
                    <button class="cw-close-chat" title="Cerrar chat">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="cw-messages"></div>
            <div class="cw-input-container">
                <div class="cw-input-wrapper">
                    <button class="cw-emoji-btn" title="Emojis">
                        <i class="far fa-smile"></i>
                    </button>
                    <div class="cw-emoji-picker"></div>
                    <input type="text" class="cw-input" placeholder="Escribe un mensaje...">
                    <button class="cw-send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;

        // Configurar el botón de invitación
        const inviteBtn = chatContainer.querySelector('.cw-game-invite-btn');
        inviteBtn.onclick = () => {
            if (!this.pendingChallenges.has(userId)) {
                this.handleGameInvite(userId, username, channelName);
            }
        };

        // Cargar emojis en el picker
        const emojiPicker = chatContainer.querySelector('.cw-emoji-picker');
        if (emojiPicker) {
            emojiPicker.innerHTML = this.getCommonEmojis();
        }

        this.container.querySelector('.cw-tab-content').appendChild(chatContainer);
        this.setupChatListeners(chatContainer, userId, channelName);
        return chatContainer;
    }

    handleGameInvite(userId, username, channelName) {
        // Evitar múltiples invitaciones
        if (this.pendingChallenges.has(userId)) {
            return;
        }

        this.pendingChallenges.add(userId);

        webSocketService.send({
            type: 'challenge_action',
            action: 'challenge',
            from_user_id: parseInt(localStorage.getItem('user_id')),
            to_username: username,
            channel_name: channelName,
            message: `${localStorage.getItem('username')} te ha invitado a jugar una partida!`
        });

        // Mensaje para el emisor
        this.addMessageToChat(userId, {
            content: '🎮 Has enviado una invitación para jugar',
            user_id: parseInt(localStorage.getItem('user_id')),
            username: 'Sistema',
            isSystem: true
        });

        // Limpiar la invitación después de 1 minuto
        setTimeout(() => {
            this.pendingChallenges.delete(userId);
        }, 60000);
    }

    handleChallengeAction(data) {
        const { action, from_user_id, to_user_id, message, channel_name, game_id } = data;
        const currentUserId = parseInt(localStorage.getItem('user_id'));
        const otherUserId = currentUserId === from_user_id ? to_user_id : from_user_id;

        if (action === 'challenge' && currentUserId === to_user_id) {
            // Crear un ID único para los botones
            const responseId = `challenge-${Date.now()}`;
            const responseButtons = `
                <div class="cw-challenge-response" id="${responseId}">
                    <button class="cw-accept-challenge" onclick="(e => {
                        e.target.closest('.cw-challenge-response').remove();
                        window.acceptChallenge(${from_user_id}, '${data.from_username}', '${channel_name}');
                    })(event)">
                        <i class="fas fa-check"></i> Aceptar
                    </button>
                    <button class="cw-reject-challenge" onclick="(e => {
                        e.target.closest('.cw-challenge-response').remove();
                        window.rejectChallenge(${from_user_id}, '${data.from_username}', '${channel_name}');
                    })(event)">
                        <i class="fas fa-times"></i> Rechazar
                    </button>
                </div>
            `;

            this.addMessageToChat(from_user_id, {
                content: message,
                user_id: from_user_id,
                username: data.from_username,
                isSystem: true
            });

            this.addMessageToChat(from_user_id, {
                content: responseButtons,
                user_id: from_user_id,
                username: 'Sistema',
                isSystem: true
            });

            // Auto-eliminar botones después de 30 segundos
            setTimeout(() => {
                const responseDiv = document.getElementById(responseId);
                if (responseDiv) {
                    responseDiv.remove();
                    // Añadir mensaje de expiración
                    this.addMessageToChat(from_user_id, {
                        content: 'La invitación ha expirado',
                        user_id: 'system',
                        username: 'Sistema',
                        isSystem: true
                    });
                }
            }, 30000);
        } else if (action === 'accept' || action === 'reject') {
            // Mostrar respuesta para ambos usuarios
            this.addMessageToChat(otherUserId, {
                content: message,
                user_id: from_user_id,
                username: 'Sistema',
                isSystem: true
            });

            if (action === 'accept' && game_id) {
                // Cambiar la navegación para usar el router del cliente
                setTimeout(() => {
                    window.history.pushState(null, '', `/game/${game_id}`);
                    window.dispatchEvent(new PopStateEvent('popstate'));
                }, 1500);
            }
        }

        this.pendingChallenges.delete(otherUserId);
    }

    getCommonEmojis() {
        const emojis = ['😊', '😂', '❤️', '👍', '😅', '🎉', '🤔', '😎', 
                       '😍', '👋', '🤗', '👌', '🙌', '✨', '💪', '🤝'];
        return emojis.map(emoji => 
            `<div class="cw-emoji-item" data-emoji="${emoji}">${emoji}</div>`
        ).join('');
    }
}