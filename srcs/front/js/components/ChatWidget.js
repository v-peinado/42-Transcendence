import { webSocketService } from '../services/WebSocketService.js';
import AuthService from '../services/AuthService.js';
import { UserList } from '../views/chat/chatcomponents/UserList.js';
import { FriendList } from '../views/chat/chatcomponents/FriendList.js';
import { friendService } from '../services/FriendService.js';

export class ChatWidget {
    static instance = null;
    static syncPromise = null;
    
    constructor() {
        if (ChatWidget.instance) {
            return ChatWidget.instance;
        }
        ChatWidget.instance = this;
        
        this.container = null;
        this.isMinimized = true;
        this.unreadCount = parseInt(localStorage.getItem('chat_unread_count') || '0');
        
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
                                <button class="cw-tab-btn cw-active" data-tab="chat">
                                    <i class="fas fa-comments"></i> Chat
                                </button>
                                <button class="cw-tab-btn" data-tab="users">
                                    <i class="fas fa-users"></i> Usuarios
                                </button>
                                <button class="cw-tab-btn" data-tab="friends">
                                    <i class="fas fa-user-friends"></i> Amigos
                                </button>
                                <button class="cw-tab-btn" data-tab="requests">
                                    <i class="fas fa-user-plus"></i> Solicitudes
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

            // Inicializar UserList y configurar eventos de usuarios
            this.userList = new UserList(this.container);
            this.friendList = new FriendList(this.container);
            
            // Limpiar listeners duplicados
            webSocketService.off('friend_list_update');
            webSocketService.off('pending_friend_requests');
            webSocketService.off('sent_friend_requests');
            webSocketService.off('error');

            // Añadir un solo listener para friend_list_update
            webSocketService.on('friend_list_update', (data) => {
                console.log('Lista de amigos actualizada:', data);
                if (data.friends) {
                    const currentUserId = parseInt(localStorage.getItem('user_id'));
                    const friendIds = data.friends.map(f => 
                        f.user1_id === currentUserId ? f.user2_id : f.user1_id
                    );
                    this.userList.setCurrentFriends(friendIds);
                    this.friendList.updateFriendsList(data);
                }
            });

            // Configurar eventos de WebSocket para la gestión de amigos
            webSocketService.on('pending_friend_requests', (data) => {
                console.log('Solicitudes pendientes recibidas:', data);
                this.friendList.updatePendingRequests(data);
            });

            webSocketService.on('sent_friend_requests', (data) => {
                console.log('Solicitudes enviadas:', data);
                this.userList.updateSentRequests(data.pending || []);
            });

            // Solicitar datos iniciales
            webSocketService.send({ type: 'get_pending_requests' });
            webSocketService.send({ type: 'get_sent_requests' });
            webSocketService.send({ type: 'get_friend_list' });

            // Manejar errores
            webSocketService.on('error', (data) => {
                console.error('Error del servidor:', data.message);
                // Opcional: Mostrar notificación al usuario
            });

            // Solicitar datos iniciales
            webSocketService.send({ type: 'get_pending_requests' });
            webSocketService.send({ type: 'get_sent_requests' });
            webSocketService.send({ type: 'get_friend_list' });

            // Añadir callback para el chat privado
            this.userList.onUserChat((userId, username) => {
                // Aquí puedes manejar el inicio de un chat privado si lo deseas
                console.log('Solicitud de chat privado:', userId, username);
            });

            // Suscribirse a eventos de WebSocket
            webSocketService.on('user_list', (data) => {
                console.log('Lista de usuarios recibida en widget:', data);
                this.userList.updateList(data);
            });

            webSocketService.on('user_status', (data) => {
                console.log('Estado de usuario actualizado:', data);
                this.userList.updateUserStatus(data.user_id, data.is_online);
            });

            webSocketService.on('friend_request_response', (data) => {
                console.log('Respuesta de solicitud de amistad:', data);
                // Actualizar la lista de usuarios si es necesario
                if (data.success) {
                    this.userList.updateSentRequests(data.sent_requests || []);
                }
            });

            webSocketService.on('friend_list', (data) => {
                console.log('Lista de amigos recibida:', data);
                this.friendList.updateFriendsList(data);
            });

            webSocketService.on('friend_requests', (data) => {
                console.log('Solicitudes de amistad recibidas:', data);
                this.friendList.updatePendingRequests(data);
            });

            // Suscribirse a eventos de WebSocket para amistades
            webSocketService.on('pending_friend_requests', (data) => {
                console.log('Solicitudes pendientes recibidas:', data);
                this.friendList.updatePendingRequests(data);
            });

            webSocketService.on('sent_friend_requests', (data) => {
                console.log('Solicitudes enviadas:', data);
                this.userList.updateSentRequests(data.pending || []);
            });

            webSocketService.on('friend_list_update', (data) => {
                console.log('Lista de amigos actualizada:', data);
                this.friendList.updateFriendsList(data);
                // Actualizar también la lista de amigos en UserList
                this.userList.setCurrentFriends(
                    new Set(data.friends.map(f => 
                        f.user1_id === parseInt(localStorage.getItem('user_id')) 
                            ? f.user2_id 
                            : f.user1_id
                    ))
                );
            });

            // Solicitar lista inicial de usuarios al conectar
            webSocketService.send({
                type: 'get_user_list'
            });

            // Solicitar listas iniciales
            webSocketService.send({ type: 'get_friend_list' });
            webSocketService.send({ type: 'get_friend_requests' });

            // Solicitar listas iniciales con el tipo correcto
            webSocketService.send({ type: 'get_pending_requests' });
            webSocketService.send({ type: 'get_sent_requests' });
            webSocketService.send({ type: 'get_friend_list' });

            // Manejar errores de WebSocket
            webSocketService.on('error', (data) => {
                console.error('Error del servidor:', data.message);
                // Aquí podrías mostrar un toast o notificación al usuario
            });

            // Manejar actualización de amigos
            webSocketService.on('friend_list_update', (data) => {
                console.log('Lista de amigos actualizada:', data);
                this.friendList.updateFriendsList(data);
                // Actualizar también UserList con la nueva lista de amigos
                if (data.friends) {
                    const currentUserId = parseInt(localStorage.getItem('user_id'));
                    const friendIds = data.friends.map(f => 
                        f.user1_id === currentUserId ? f.user2_id : f.user1_id
                    );
                    this.userList.setCurrentFriends(new Set(friendIds));
                }
            });

            // Solicitar datos iniciales con el tipo correcto
            webSocketService.send({ type: 'request_friend_list' });
            webSocketService.send({ type: 'request_pending_requests' });
            webSocketService.send({ type: 'request_sent_requests' });

            // Manejar respuestas a solicitudes de amistad
            webSocketService.on('friend_request_response', (data) => {
                console.log('Respuesta de solicitud de amistad:', data);
                if (data.success) {
                    const isAccepted = data.status === 'accepted';
                    this.userList.handleFriendRequestResponse(data.user_id, isAccepted);
                    
                    // Actualizar listas
                    webSocketService.send({ type: 'get_friend_list' });
                    webSocketService.send({ type: 'get_sent_requests' });
                }
            });

            // Configurar cambio de tabs
            const tabButtons = this.container.querySelectorAll('.cw-tab-btn');
            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    // Remover active de todos los tabs
                    tabButtons.forEach(btn => btn.classList.remove('cw-active'));
                    this.container.querySelectorAll('.cw-tab-pane').forEach(pane => 
                        pane.classList.remove('cw-active'));
                    
                    // Activar tab seleccionado
                    button.classList.add('cw-active');
                    const tabId = `${button.dataset.tab}-tab`;
                    this.container.querySelector(`#${tabId}`).classList.add('cw-active');
                });
            });

            // Obtener referencias a elementos
            const toggleBtn = this.container.querySelector('.cw-toggle-btn');
            const chatWidget = this.container.querySelector('.cw-widget');
            const minimizeBtn = this.container.querySelector('.cw-minimize-btn');
            const messageInput = this.container.querySelector('#widget-message-input');
            const sendButton = this.container.querySelector('#widget-send-button');
            const messagesContainer = this.container.querySelector('#widget-messages');

            // Configurar eventos
            toggleBtn.addEventListener('click', () => {
                this.isMinimized = !this.isMinimized;
                chatWidget.classList.toggle('visible');
                toggleBtn.querySelector('i').classList.toggle('fa-comments');
                toggleBtn.querySelector('i').classList.toggle('fa-times');
                
                if (!this.isMinimized) {
                    // Asegurar que el widget sea visible
                    chatWidget.style.display = 'block';
                    this.resetUnreadCount();
                } else {
                    // Asegurar que el widget esté oculto
                    chatWidget.style.display = 'none';
                }
                
                localStorage.setItem('chat_minimized', this.isMinimized.toString());
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
                messageElement.className = `cw-message ${
                    data.user_id === parseInt(localStorage.getItem('user_id')) 
                        ? 'cw-message-my' 
                        : 'cw-message-other'
                }`;
                
                messageElement.innerHTML = `
                    <span class="cw-message-username">${data.username}</span>
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

            // Configurar listeners de WebSocket para usuarios
            webSocketService.on('user_list', (data) => {
                console.log('Lista de usuarios recibida:', data);
                this.userList.updateList(data);
            });

            webSocketService.on('user_status', (data) => {
                this.userList.updateUserStatus(data.user_id, data.is_online);
            });

            // Asegurarnos de que el WebSocket esté conectado antes de empezar
            if (!webSocketService.socket || webSocketService.socket.readyState !== WebSocket.OPEN) {
                await webSocketService.connect('general');
            }

            // Inicializar estado al montar
            const lastState = localStorage.getItem('chat_minimized');
            if (lastState === 'false') {
                this.isMinimized = false;
                chatWidget.classList.add('visible');
                chatWidget.style.display = 'block';
                this.resetUnreadCount();
            }

            document.body.appendChild(this.container);

        } catch (error) {
            console.error('Error durante el montaje del chat:', error);
        }
    }

    incrementUnreadCount() {
        this.unreadCount++;
        // Guardar en localStorage
        localStorage.setItem('chat_unread_count', this.unreadCount.toString());
        this.updateNotificationBadge();
    }

    resetUnreadCount() {
        this.unreadCount = 0;
        // Limpiar en localStorage
        localStorage.setItem('chat_unread_count', '0');
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
            this.container.querySelector('.cw-widget').classList.add('visible');
            this.resetUnreadCount();
        }
    }
}
