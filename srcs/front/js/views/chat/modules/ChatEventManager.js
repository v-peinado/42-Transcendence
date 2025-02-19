import { webSocketService } from '../../../services/WebSocketService.js';

export class ChatEventManager {
    constructor() {
        this.components = {
            generalChat: null,
            privateChat: null,
            userList: null,
            friendList: null
        };
    }

    async initialize(components) {
        this.components = components;
        
        // Configurar callbacks entre componentes
        this.setupCallbacks();
        
        // Conectar WebSocket
        await webSocketService.connect('general');
        
        // Registrar manejadores de eventos
        this.registerWebSocketListeners();
        
        // Solicitar datos iniciales
        this.requestInitialData();

        this.setupCustomEventListeners();
    }

    setupCallbacks() {
        // Configurar callback para chat privado desde lista de usuarios
        this.components.userList.onUserChat((userId, username) => {
            this.handlePrivateChatRequest(userId, username);
        });

        // Configurar callback para chat privado desde lista de amigos
        this.components.friendList.onChat((userId, username) => {
            this.handlePrivateChatRequest(userId, username);
        });
    }

    registerWebSocketListeners() {
        // Eventos de chat
        webSocketService.on('chat_message', this.handleChatMessage.bind(this));
        webSocketService.on('private_channels', this.handlePrivateChannels.bind(this));
        
        // Eventos de lista de usuarios
        webSocketService.on('user_list', this.handleUserList.bind(this));
        webSocketService.on('user_status', this.handleUserStatus.bind(this));
        
        // Eventos de amigos
        webSocketService.on('friend_list_update', this.handleFriendListUpdate.bind(this));
        webSocketService.on('friend_request_sent', this.handleFriendRequestSent.bind(this));
        webSocketService.on('friend_request_received', this.handleFriendRequestReceived.bind(this));
        webSocketService.on('friend_request_accepted', this.handleFriendRequestAccepted.bind(this));
        webSocketService.on('friendship_deleted', this.handleFriendshipDeleted.bind(this));
        webSocketService.on('pending_friend_requests', this.handlePendingRequests.bind(this));
        webSocketService.on('sent_friend_requests', this.handleSentRequests.bind(this));
        
        // Eventos de error
        webSocketService.on('error', this.handleError.bind(this));
    }

    requestInitialData() {
        const requests = [
            { type: 'request_friend_list' },
            { type: 'request_pending_requests' },
            { type: 'request_user_list' }
        ];

        requests.forEach((request, index) => {
            setTimeout(() => {
                webSocketService.send(request);
            }, index * 100);
        });
    }

    // Manejadores de eventos de chat
    handleChatMessage(data) {
        if (data.channel_name?.startsWith('dm_')) {
            this.components.privateChat.handleHistoricalMessage(data);
        } else {
            this.components.generalChat.addMessage(data);
        }
    }

    handlePrivateChannels(data) {
        this.components.privateChat.updateChannelsList(data);
    }

    // Manejadores de eventos de usuarios
    handleUserList(data) {
        this.components.userList.updateList(data);
    }

    handleUserStatus(data) {
        this.components.userList.updateUserStatus(data.user_id, data.is_online);
        this.components.friendList.updateFriendStatus(data.user_id, data.is_online);
    }

    // Manejadores de eventos de amigos
    handleFriendListUpdate(data) {
        this.components.friendList.updateFriendsList(data);
        this.components.userList.setCurrentFriends(
            data.friends.map(f => f.user1_id === this.getCurrentUserId() ? f.user2_id : f.user1_id)
        );
        this.components.userList.setCurrentFriendships(data.friends);
    }

    handleFriendRequestSent(data) {
        // Actualizar UI después de enviar solicitud
        this.components.userList.updateList(data);
    }

    handleFriendRequestReceived(data) {
        this.components.friendList.updatePendingRequests(data);
    }

    handleFriendRequestAccepted(data) {
        webSocketService.send({ type: 'request_friend_list' });
        webSocketService.send({ type: 'request_user_list' });
    }

    handleFriendshipDeleted(data) {
        webSocketService.send({ type: 'request_friend_list' });
        webSocketService.send({ type: 'request_user_list' });
    }

    handlePendingRequests(data) {
        this.components.friendList.updatePendingRequests(data);
    }

    handleSentRequests(data) {
        // Actualizar UI para mostrar solicitudes enviadas
        this.components.userList.updateSentRequests(data.pending);
    }

    // Manejador de errores
    handleError(data) {
        console.error('Error en el chat:', data.message);
        if (data.type === 'auth_error') {
            // Manejar errores de autenticación
            window.location.href = '/login';
        } else {
            // Mostrar error en la UI
            alert(data.message);
        }
    }

    // Utilidades
    handlePrivateChatRequest(userId, username) {
        const currentUserId = this.getCurrentUserId();
        const minId = Math.min(currentUserId, userId);
        const maxId = Math.max(currentUserId, userId);
        
        webSocketService.send({
            type: 'create_private_channel',
            user1_id: minId,
            user2_id: maxId
        });

        this.components.privateChat.showChat(`dm_${minId}_${maxId}`, username);
    }

    getCurrentUserId() {
        return parseInt(localStorage.getItem('user_id'));
    }

    setupCustomEventListeners() {
        document.addEventListener('start-private-chat', (event) => {
            const { channelName, username, userId } = event.detail;
            
            // Cambiar el manejo del evento private_channels para que sea una única vez
            const handlePrivateChannel = (data) => {
                const channelExists = data.channels.some(channel => channel.name === channelName);
                if (channelExists) {
                    this.components.privateChat.showChat(channelName, username);
                    // Remover el listener después de usarlo
                    webSocketService.off('private_channels', handlePrivateChannel);
                }
            };

            webSocketService.on('private_channels', handlePrivateChannel);

            // Suscribirse al canal
            webSocketService.send({
                type: 'subscribe_to_chat',
                channel_name: channelName
            });
        });
    }
}