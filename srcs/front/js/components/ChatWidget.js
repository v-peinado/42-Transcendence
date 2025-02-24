import { webSocketService } from '../services/WebSocketService.js';
import AuthService from '../services/AuthService.js';
import { UserList } from '../views/chat/chatcomponents/UserList.js';
import { FriendList } from '../views/chat/chatcomponents/FriendList.js';
import { PrivateChat } from '../views/chat/chatcomponents/PrivateChat.js'; // Añadir esta importación
import { friendService } from '../services/FriendService.js';
import { blockService } from '../services/BlockService.js';

export class ChatWidget {
    static instance = null;
    static syncPromise = null;
    
    constructor() {
        if (ChatWidget.instance) {
            return ChatWidget.instance;
        }
        ChatWidget.instance = this;
        
        this.container = null;
        this.isMinimized = localStorage.getItem('chat_minimized') !== 'false';
        
        // Restaurar el contador solo si el widget está minimizado
        this.unreadCount = this.isMinimized ? 
            parseInt(localStorage.getItem('chat_unread_count') || '0') : 
            0;

        this.lastMessageTimestamp = Date.now();
    }

    async syncUserData() {
        if (ChatWidget.syncPromise) {
            console.log('Sincronización en curso, esperando...');
            return ChatWidget.syncPromise;
        }

        console.log('Iniciando sincronización de datos de usuario...');
        
        // Añadir un timeout para la sincronización
        const timeout = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Timeout en sincronización')), 5000);
        });

        ChatWidget.syncPromise = (async () => {
            try {
                const response = await Promise.race([
                    fetch('/api/user/profile'),
                    timeout
                ]);

                if (!response.ok) {
                    throw new Error(`Error en la respuesta: ${response.status}`);
                }

                const userData = await response.json();
                console.log('Datos de usuario recibidos:', userData);
                
                if (!userData || !userData.id) {
                    throw new Error('Datos de usuario inválidos');
                }

                localStorage.setItem('user_id', userData.id);
                localStorage.setItem('username', userData.username);
                
                console.log('Sincronización completada - ID:', userData.id, 'Username:', userData.username);
                return userData;

            } catch (error) {
                console.error('Error en sincronización:', error);
                // Intentar usar datos existentes si están disponibles
                const existingId = localStorage.getItem('user_id');
                const existingUsername = localStorage.getItem('username');
                
                if (existingId && existingUsername) {
                    console.log('Usando datos existentes:', { id: existingId, username: existingUsername });
                    return { id: existingId, username: existingUsername };
                }
                throw error;
            } finally {
                ChatWidget.syncPromise = null;
                console.log('Proceso de sincronización finalizado');
            }
        })();

        return ChatWidget.syncPromise;
    }

    static async initialize() {
        // Validar autenticación primero, similar a ChatView
        if (!await this.validateAuth()) return null;

        const widget = new ChatWidget();
        if (!widget.container && !window.location.pathname.includes('/chat')) {
            await widget.mount();
        }
        return widget;
    }

    static async validateAuth() {
        if (localStorage.getItem('isAuthenticated') !== 'true') {
            console.log('Usuario no autenticado');
            return false;
        }
        
        try {
            const profile = await AuthService.getUserProfile();
            if (profile?.id) {
                localStorage.setItem('user_id', profile.id.toString());
                localStorage.setItem('username', profile.username);
                console.log('Perfil de usuario cargado:', profile);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error al obtener el perfil:', error);
            return false;
        }
    }

    async mount() {
        try {
            // Verificar perfil antes de montar
            if (!localStorage.getItem('user_id')) {
                if (!await ChatWidget.validateAuth()) {
                    console.error('No se pudo validar la autenticación');
                    return;
                }
            }

            console.log('Montando chat con ID de usuario:', localStorage.getItem('user_id'));
            
            // Crear el contenedor del widget
            this.container = document.createElement('div');
            this.container.className = 'cw-container';  // Cambiado de chat-widget-container a cw-container
            
            // Crear la estructura completa del widget
            this.container.innerHTML = `
                <div class="cw-widget">
                    <div class="cw-content">
                        <header class="cw-header">
                            <nav class="cw-tabs">
                                <button class="cw-tab-btn cw-active" data-tab="chat" title="Chat general">
                                    <i class="fas fa-comments"></i>
                                </button>
                                <button class="cw-tab-btn" data-tab="users" title="Lista de usuarios">
                                    <i class="fas fa-users"></i>
                                </button>
                                <button class="cw-tab-btn" data-tab="friends" title="Lista de amigos">
                                    <i class="fas fa-user-friends"></i>
                                </button>
                                <button class="cw-tab-btn" data-tab="requests" title="Solicitudes de amistad">
                                    <i class="fas fa-user-plus"></i>
                                    <span class="cw-requests-badge"></span>
                                </button>
                            </nav>
                            <button class="cw-minimize-btn" title="Minimizar">
                                <i class="fas fa-minus"></i>
                            </button>
                        </header>
                        
                        <div class="cw-tab-content">
                            <div id="chat-tab" class="cw-tab-pane cw-active">
                                <div id="widget-messages" class="cw-messages"></div>
                                <div class="cw-input-container">
                                    <div class="cw-input-wrapper">
                                        <button class="cw-emoji-btn" title="Emojis">
                                            <i class="far fa-smile"></i>
                                        </button>
                                        <div class="cw-emoji-picker">
                                            ${this.getCommonEmojis()}
                                        </div>
                                        <input type="text" 
                                            id="widget-message-input" 
                                            class="cw-input" 
                                            placeholder="Escribe un mensaje..." 
                                            autocomplete="off">
                                        <button type="submit" 
                                                id="widget-send-button" 
                                                class="cw-send-btn">
                                            <i class="fas fa-paper-plane"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <div id="users-tab" class="cw-tab-pane">
                                <div id="widget-users-list" class="cw-users-list"></div>
                            </div>

                            <div id="friends-tab" class="cw-tab-pane">
                                <div id="widget-friends-list" class="cw-users-list"></div>
                            </div>

                            <div id="requests-tab" class="cw-tab-pane">
                                <div id="widget-requests-list" class="cw-users-list"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <button class="cw-toggle-btn">
                    <i class="fas fa-comments"></i>
                    <span class="cw-notification"></span>
                </button>
            `;

            this.container.innerHTML += `
                <style>
                    .cw-block-notification {
                        position: fixed;
                        bottom: 80px;
                        right: 20px;
                        z-index: 10000;
                        animation: slideIn 0.3s ease-out;
                    }

                    .cw-block-msg {
                        background-color: #ff4444;
                        color: white;
                        padding: 12px 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                        font-size: 14px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }

                    .cw-block-msg i {
                        font-size: 16px;
                    }

                    .fade-out {
                        opacity: 0;
                        transition: opacity 0.5s ease-out;
                    }

                    @keyframes slideIn {
                        from {
                            transform: translateY(100%);
                            opacity: 0;
                        }
                        to {
                            transform: translateY(0);
                            opacity: 1;
                        }
                    }

                    .cw-message-system {
                        text-align: center;
                        margin: 10px 0;
                    }
                    
                    .cw-system-message {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        background-color: #ff44442e;
                        color: #ff4444;
                        padding: 8px 16px;
                        border-radius: 16px;
                        font-size: 13px;
                    }
                    
                    .cw-system-message i {
                        font-size: 14px;
                    }
                </style>
            `;

            // Inicializar componentes (eliminar duplicados y configurar correctamente)
            this.userList = new UserList(this.container);
            this.friendList = new FriendList(this.container);
            this.privateChat = new PrivateChat(this.container);

            // Configurar callbacks inmediatamente después de inicializar
            this.userList.onUserChat((userId, username) => {
                console.log('Callback de chat recibido para:', userId, username);
                this.privateChat.createPrivateChat(userId, username);
            });

            this.friendList.onChat((userId, username) => {
                console.log('Callback de chat de amigo recibido para:', userId, username);
                this.privateChat.createPrivateChat(userId, username);
            });

            // Limpiar TODOS los listeners existentes
            this.clearAllWebSocketListeners();

            // Configurar todos los listeners una sola vez
            this.setupWebSocketListeners();
            
            // Configurar eventos UI
            this.setupUIEventListeners();

            // Solicitar datos iniciales
            this.requestInitialData();

            document.body.appendChild(this.container);
            
            // Mostrar widget si estaba abierto y actualizar UI
            if (!this.isMinimized) {
                const chatWidget = this.container.querySelector('.cw-widget');
                chatWidget.classList.add('visible');
                chatWidget.style.display = 'block';
                this.resetUnreadCount();
                
                const toggleBtn = this.container.querySelector('.cw-toggle-btn');
                if (toggleBtn) {
                    toggleBtn.querySelector('i').classList.remove('fa-comments');
                    toggleBtn.querySelector('i').classList.add('fa-times');
                }
            } else {
                // Actualizar badge si hay notificaciones pendientes
                this.updateNotificationBadge();
            }

        } catch (error) {
            console.error('Error durante el montaje del chat:', error);
        }
    }

    clearAllWebSocketListeners() {
        [
            'chat_message',
            'private_channels',
            'friend_list_update',
            'pending_friend_requests',
            'sent_friend_requests',
            'user_list',
            'user_status',
            'error',
            'blocked',
            'unblocked',
            'blocked_users',
            'blocked_notification'
        ].forEach(event => webSocketService.off(event));
    }

    setupUIEventListeners() {
        // Obtener referencias a elementos
        const toggleBtn = this.container.querySelector('.cw-toggle-btn');
        const chatWidget = this.container.querySelector('.cw-widget');
        const minimizeBtn = this.container.querySelector('.cw-minimize-btn');
        const messageInput = this.container.querySelector('#widget-message-input');
        const sendButton = this.container.querySelector('#widget-send-button');

        // Configurar evento de toggle
        toggleBtn.addEventListener('click', () => {
            this.isMinimized = !this.isMinimized;
            chatWidget.classList.toggle('visible');
            toggleBtn.querySelector('i').classList.toggle('fa-comments');
            toggleBtn.querySelector('i').classList.toggle('fa-times');
            
            if (!this.isMinimized) {
                chatWidget.style.display = 'block';
                this.resetUnreadCount();
            } else {
                chatWidget.style.display = 'none';
            }
            
            localStorage.setItem('chat_minimized', this.isMinimized.toString());
        });

        // Configurar evento de minimizar
        minimizeBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Evitar que el click se propague
            this.isMinimized = true;
            chatWidget.classList.remove('visible');
            chatWidget.style.display = 'none';
            toggleBtn.querySelector('i').classList.remove('fa-times');
            toggleBtn.querySelector('i').classList.add('fa-comments');
            
            // Guardar estado
            localStorage.setItem('chat_minimized', 'true');
        });

        // Configurar envío de mensajes
        const sendMessage = async () => {
            const messageInput = this.container.querySelector('#widget-message-input');
            const message = messageInput.value.trim();
            if (!message) return;

            const userId = localStorage.getItem('user_id');
            if (!userId) {
                console.error('ID de usuario no encontrado, reintentando sincronización...');
                await this.syncUserData();
                if (!localStorage.getItem('user_id')) {
                    console.error('No se pudo obtener el ID de usuario');
                    return;
                }
            }

            const messageData = {
                type: 'chat_message',
                content: message,
                room: 'general',
                channel_name: 'chat_general',
                user_id: parseInt(userId),
                username: localStorage.getItem('username')
            };

            console.log('Enviando mensaje con datos:', messageData);
            webSocketService.send(messageData);
            messageInput.value = '';
        };

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Añadir manejador de tabs
        const tabButtons = this.container.querySelectorAll('.cw-tab-btn');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remover active de todos los tabs y panes
                tabButtons.forEach(btn => btn.classList.remove('cw-active'));
                this.container.querySelectorAll('.cw-tab-pane').forEach(pane => 
                    pane.classList.remove('cw-active')
                );
                
                // Activar tab y pane seleccionados
                button.classList.add('cw-active');
                const tabId = `${button.dataset.tab}-tab`;
                const targetPane = this.container.querySelector(`#${tabId}`);
                if (targetPane) {
                    targetPane.classList.add('cw-active');
                }
                
                // Actualizar contenido según el tab
                switch(button.dataset.tab) {
                    case 'users':
                        this.userList.updateList(this.userList.lastUserData);
                        break;
                    case 'friends':
                        webSocketService.send({ type: 'get_friend_list' });
                        break;
                    case 'requests':
                        webSocketService.send({ type: 'get_pending_requests' });
                        break;
                }
            });
        });

        // Añadir listener para nuevos mensajes privados
        document.addEventListener('new-private-message', (event) => {
            const { userId, username, message } = event.detail;
            
            // Si el widget está minimizado, mostrar notificación
            if (this.isMinimized) {
                this.incrementUnreadCount();
                // Opcional: Mostrar una notificación del sistema
                if (Notification.permission === 'granted') {
                    new Notification(`Mensaje de ${username}`, {
                        body: message,
                        icon: '/favicon.ico'
                    });
                }
            }
        });

        // Emoji picker functionality
        const emojiBtn = this.container.querySelector('.cw-emoji-btn');
        const emojiPicker = this.container.querySelector('.cw-emoji-picker');
        const input = this.container.querySelector('#widget-message-input');

        if (emojiBtn && emojiPicker && input) {
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
    }

    setupWebSocketListeners() {
        // Chat messages (un solo listener)
        webSocketService.on('chat_message', (data) => {
            console.log('Mensaje recibido:', data);
            // Marcar si es un mensaje nuevo o del historial
            const isNewMessage = !data.timestamp || data.timestamp >= this.lastMessageTimestamp;
            
            if (data.channel_name?.startsWith('dm_')) {
                this.privateChat.handlePrivateMessage(data);
            } else {
                this.handleGeneralChatMessage(data, isNewMessage);
            }
        });

        // Modificar el listener de blocked
        webSocketService.on('blocked', (data) => {
            console.log('Evento de bloqueo recibido:', data);
            
            // Si soy yo el bloqueado
            if (data.blocked_user_id === parseInt(localStorage.getItem('user_id'))) {
                blockService.handleBlockedUsers({
                    type: 'blocked_by',
                    user_id: data.user_id
                });
            }
            
            if (this.privateChat.activeChats.has(data.user_id)) {
                this.privateChat.closeChat(data.user_id);
            }
            
            // Actualizar la lista de usuarios
            this.userList.updateList(this.userList.lastUserData);
        });

        // Private channels
        webSocketService.on('private_channels', (data) => {
            console.log('Canales privados recibidos:', data);
            if (data.channels) {
                data.channels.forEach(channel => {
                    const otherUser = channel.members.find(m => 
                        m.id !== parseInt(localStorage.getItem('user_id'))
                    );
                    if (otherUser) {
                        // Solo crear el chat si no existe
                        if (!this.privateChat.activeChats.has(otherUser.id)) {
                            this.privateChat.createPrivateChat(otherUser.id, otherUser.username);
                        }
                    }
                });
            }
        });

        // Friend related events
        webSocketService.on('friend_list_update', (data) => {
            if (data.friends) {
                const currentUserId = parseInt(localStorage.getItem('user_id'));
                const friendIds = data.friends.map(f => 
                    f.user1_id === currentUserId ? f.user2_id : f.user1_id
                );
                this.userList.setCurrentFriends(friendIds);
                this.friendList.updateFriendsList(data);
            }
        });

        // User related events
        webSocketService.on('user_list', (data) => {
            this.userList.updateList(data);
        });

        webSocketService.on('user_status', (data) => {
            this.userList.updateUserStatus(data.user_id, data.is_online);
        });

        // Error handling
        webSocketService.on('error', (data) => {
            console.error('Error del servidor:', data.message);
        });

        // Friend requests events
        webSocketService.on('pending_friend_requests', (data) => {
            console.log('Solicitudes pendientes recibidas:', data);
            this.friendList.updatePendingRequests(data);
        });

        webSocketService.on('sent_friend_requests', (data) => {
            console.log('Solicitudes enviadas:', data);
            this.userList.updateSentRequests(data.pending || []);
        });

        webSocketService.on('friend_request_response', (data) => {
            console.log('Respuesta de solicitud de amistad:', data);
            if (data.success) {
                const isAccepted = data.status === 'accepted';
                this.userList.handleFriendRequestResponse(data.user_id, isAccepted);
                
                // Actualizar listas después de responder a una solicitud
                webSocketService.send({ type: 'get_friend_list' });
                webSocketService.send({ type: 'get_pending_requests' });
                webSocketService.send({ type: 'get_sent_requests' });
            }
        });

        // Añadir listener para historial de mensajes
        webSocketService.on('chat_history', (data) => {
            if (data.messages && data.channel_name) {
                data.messages.forEach(msg => {
                    this.privateChat.handlePrivateMessage({
                        ...msg,
                        channel_name: data.channel_name
                    });
                });
            }
        });

        // Añadir listener para usuarios bloqueados
        webSocketService.on('blocked_users', (data) => {
            console.log('Lista de usuarios bloqueados recibida:', data);
            blockService.handleBlockedUsersList(data.blocked_users);
        });

        webSocketService.on('unblocked', (data) => {
            console.log('Usuario desbloqueado:', data);
            blockService.handleBlockedUsers({
                type: 'unblocked',
                user_id: data.user_id,
                username: data.username
            });
            this.userList.updateList(this.userList.lastUserData);
            webSocketService.send({ type: 'get_blocked_users' });
        });

        // Añadir listener para notificaciones de bloqueo
        webSocketService.on('blocked_notification', (data) => {
            const notification = document.createElement('div');
            notification.className = 'cw-block-notification';
            notification.innerHTML = `
                <div class="cw-block-msg">
                    <i class="fas fa-ban"></i>
                    <span>Has sido bloqueado por ${data.blocker_username}</span>
                </div>
            `;

            document.body.appendChild(notification);

            // Remover la notificación después de 5 segundos
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 500);
            }, 5000);
        });
    }

    requestInitialData() {
        const requests = [
            { type: 'get_user_list' },
            { type: 'get_friend_list' },
            { type: 'get_pending_requests' },
            { type: 'get_sent_requests' }
        ];

        // Enviar solicitudes con un pequeño retraso entre ellas
        requests.forEach((request, index) => {
            setTimeout(() => {
                console.log('Solicitando datos:', request.type);
                webSocketService.send(request);
            }, index * 100);
        });
    }

    handleGeneralChatMessage(data, isNewMessage = true) {
        const messageContent = data.message || data.content;
        if (!messageContent) return;
        
        const messageElement = document.createElement('div');
        const messageClass = data.user_id === parseInt(localStorage.getItem('user_id')) 
            ? 'cw-message cw-message-my' 
            : 'cw-message cw-message-other';
        
        messageElement.className = messageClass;
        messageElement.innerHTML = `
            <span class="cw-message-username">${data.username}</span>
            ${messageContent}
        `;
        
        const messagesContainer = this.container.querySelector('#widget-messages');
        if (messagesContainer) {
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // Solo incrementar para mensajes nuevos de otros usuarios cuando está minimizado
            if (this.isMinimized && 
                data.user_id !== parseInt(localStorage.getItem('user_id')) && 
                isNewMessage) {
                this.incrementUnreadCount();
            }
        }
    }

    incrementUnreadCount() {
        this.unreadCount++;
        if (this.isMinimized) {
            localStorage.setItem('chat_unread_count', this.unreadCount.toString());
        }
        this.updateNotificationBadge();
    }

    resetUnreadCount() {
        this.unreadCount = 0;
        localStorage.removeItem('chat_unread_count');
        this.updateNotificationBadge();
    }

    updateNotificationBadge() {
        const toggleBtn = this.container.querySelector('.cw-toggle-btn');
        let badge = toggleBtn.querySelector('.cw-notification');
        
        if (this.unreadCount > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'cw-notification';
                toggleBtn.appendChild(badge);
            }
            badge.textContent = this.unreadCount > 9 ? '9+' : this.unreadCount;
        } else if (badge) {
            badge.remove();
        }
    }

    // Añadir método para inicializar el estado del widget
    initializeWidgetState() {
        const lastState = localStorage.getItem('chat_minimized');
        if (lastState === 'false') {
            this.isMinimized = false;
            const chatWidget = this.container.querySelector('.cw-widget');
            chatWidget.classList.add('visible');
            chatWidget.style.display = 'block';
            // Resetear contador y localStorage
            this.unreadCount = 0;
            localStorage.setItem('chat_unread_count', '0');
            this.updateNotificationBadge();
            
            // Actualizar el botón de toggle
            const toggleBtn = this.container.querySelector('.cw-toggle-btn');
            toggleBtn.querySelector('i').classList.remove('fa-comments');
            toggleBtn.querySelector('i').classList.add('fa-times');
        }
    }

    // Añadir método para los emojis comunes
    getCommonEmojis() {
        const emojis = ['😊', '😂', '❤️', '👍', '😅', '🎉', '🤔', '😎', 
                        '😍', '👋', '🤗', '👌', '🙌', '✨', '💪', '🤝'];
        return emojis.map(emoji => 
            `<div class="cw-emoji-item" data-emoji="${emoji}">${emoji}</div>`
        ).join('');
    }
}
