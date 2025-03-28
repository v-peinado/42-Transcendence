import { webSocketService } from '../../../services/WebSocketService.js';
import { friendService } from '../../../services/FriendService.js';

export class FriendList {
    constructor(container) {
        // Referencias DOM
        this.container = container;
        this.friendsList = container.querySelector('#friends-list');
        this.pendingRequests = container.querySelector('#pending-requests');
        
        // Estado
        this.currentUserId = parseInt(localStorage.getItem('user_id'));
        this.onChatCallback = null;
        this.onlineUsers = new Set(); // Añadir esto

        // Suscribirse a eventos de usuarios conectados
        webSocketService.on('user_list', (data) => {
            this.onlineUsers = new Set(data.users.map(u => parseInt(u.id)));
            this.updateAllFriendsStatus();
        });

        webSocketService.on('user_online', (data) => {
            this.onlineUsers.add(parseInt(data.user_id));
            this.updateFriendStatus(parseInt(data.user_id), true);
        });

        webSocketService.on('user_offline', (data) => {
            this.onlineUsers.delete(parseInt(data.user_id));
            this.updateFriendStatus(parseInt(data.user_id), false);
        });
    }

    updateFriendsList(data) {
        const friendsList = this.container.querySelector('#widget-friends-list');
        if (!friendsList) return;

        friendsList.innerHTML = '';
        
        if (!data?.friends?.length) {
            friendsList.innerHTML = `
                <div class="cw-empty-state">
                    <i class="fas fa-user-friends"></i>
                    <p>No tienes amigos agregados</p>
                </div>
            `;
            return;
        }

        // Crear Set con los IDs de usuarios conectados
        const onlineUsers = new Set((data.users || []).map(u => parseInt(u.id)));

        data.friends.forEach(friend => {
            const isFriendUser1 = friend.user1_id === this.currentUserId;
            const friendId = parseInt(isFriendUser1 ? friend.user2_id : friend.user1_id);
            const friendUsername = isFriendUser1 ? friend.user2__username : friend.user1__username;

            // Usar this.onlineUsers en lugar de data.users
            const isOnline = this.onlineUsers.has(friendId);

            const friendElement = document.createElement('div');
            friendElement.className = 'cw-user-item';
            friendElement.dataset.userId = friendId;
            friendElement.innerHTML = `
                <div class="cw-user-info">
                    <span class="cw-user-status${isOnline ? ' online' : ''}"></span>
                    <span class="cw-username">${friendUsername}</span>
                </div>
                <div class="cw-user-actions">
                    <button class="cw-chat-btn" title="Chat privado">
                        <i class="fas fa-comment"></i>
                    </button>
                    <button class="cw-friend-remove" title="Eliminar amigo" data-friendship-id="${friend.id}">
                        <i class="fas fa-user-minus"></i>
                    </button>
                </div>
            `;

            const chatBtn = friendElement.querySelector('.cw-chat-btn');
            const removeBtn = friendElement.querySelector('.cw-friend-remove');

            chatBtn.addEventListener('click', () => {
                this.onChatCallback?.(friendId, friendUsername);
            });

            removeBtn.addEventListener('click', () => {
                const friendshipId = friend.id;  // Obtiene el ID directamente del objeto friend
                friendService.deleteFriendship(friendshipId);
                friendElement.remove();
            });

            friendsList.appendChild(friendElement);
        });
    }

    attachFriendEventListeners(friendDiv) {
        const chatBtn = friendDiv.querySelector('.chat-with-friend');
        const deleteBtn = friendDiv.querySelector('.delete-friend');

        chatBtn.addEventListener('click', () => {
            const userId = parseInt(chatBtn.dataset.userId);
            const username = chatBtn.dataset.username;
            this.onChatCallback?.(userId, username);
        });

        deleteBtn.addEventListener('click', () => {
            const friendshipId = deleteBtn.dataset.friendshipId;
            this.deleteFriendship(friendshipId);
        });
    }

    updatePendingRequests(data) {
        const requestsList = this.container.querySelector('#widget-requests-list');
        if (!requestsList) {
            console.error('No se encontró el contenedor de solicitudes');
            return;
        }

        requestsList.innerHTML = '';
        const requests = data.pending || [];

        if (!requests.length) {
            requestsList.innerHTML = `
                <div class="cw-empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No hay solicitudes pendientes</p>
                </div>
            `;
            this.updateRequestsCount(0);
            return;
        }

        requests.forEach(request => {
            const requestId = request.request_id;
            if (!requestId) {
                console.error('Solicitud sin request_id:', request);
                return;
            }

            const requestElement = document.createElement('div');
            requestElement.className = 'cw-user-item';  // Cambiado para coincidir con el estilo general
            requestElement.dataset.requestId = requestId;
            requestElement.innerHTML = `
                <div class="cw-user-info">
                    <span class="cw-username">${request.from_user_username}</span>
                    <small class="cw-request-text">quiere ser tu amigo</small>
                </div>
                <div class="cw-user-actions">
                    <button class="cw-accept-btn" title="Aceptar solicitud">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="cw-reject-btn" title="Rechazar solicitud">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;

            const acceptBtn = requestElement.querySelector('.cw-accept-btn');
            acceptBtn.addEventListener('click', async () => {
                try {
                    await friendService.acceptFriendRequest(requestId);
                    requestElement.remove();
                    this.updateRequestsCount(requestsList.querySelectorAll('.cw-request-item').length);
                } catch (error) {
                    console.error('Error al aceptar solicitud:', error);
                }
            });

            const rejectBtn = requestElement.querySelector('.cw-reject-btn');
            rejectBtn.addEventListener('click', async () => {
                try {
                    await friendService.rejectFriendRequest(requestId);
                    requestElement.remove();
                    this.updateRequestsCount(requestsList.querySelectorAll('.cw-request-item').length);
                } catch (error) {
                    console.error('Error al rechazar solicitud:', error);
                }
            });

            requestsList.appendChild(requestElement);
        });

        this.updateRequestsCount(requests.length);
    }

    updateRequestsCount(count) {
        const requestsTab = this.container.querySelector('[data-tab="requests"]');
        let badge = requestsTab.querySelector('.cw-requests-badge');
        
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'cw-requests-badge';
                requestsTab.appendChild(badge);
            }
            badge.textContent = count;
        } else if (badge) {
            badge.remove();
        }
    }

    createRequestElement(request) {
        const requestDiv = document.createElement('div');
        requestDiv.className = 'list-group-item friend-request-item';
        requestDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas fa-user me-2"></i>
                    <span>${request.from_user_username}</span>
                    <small class="text-muted ms-2">quiere ser tu amigo</small>
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-success accept-request" 
                            data-request-id="${request.request_id}">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn btn-sm btn-danger reject-request" 
                            data-request-id="${request.request_id}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        this.attachRequestEventListeners(requestDiv);
        return requestDiv;
    }

    attachRequestEventListeners(requestDiv) {
        const acceptBtn = requestDiv.querySelector('.accept-request');
        const rejectBtn = requestDiv.querySelector('.reject-request');
        const requestId = acceptBtn.dataset.requestId;

        acceptBtn.addEventListener('click', () => {
            friendService.acceptFriendRequest(requestId);
            requestDiv.remove();
        });

        rejectBtn.addEventListener('click', () => {
            friendService.rejectFriendRequest(requestId);
            requestDiv.remove();
        });
    }

    deleteFriendship(friendshipId) {
        friendService.deleteFriendship(friendshipId);
    }

    showEmptyRequestsState() {
        this.pendingRequests.innerHTML = `
            <div class="text-center text-muted p-3">
                <i class="fas fa-inbox fa-2x mb-2"></i>
                <p>No tienes solicitudes pendientes</p>
            </div>
        `;
    }

    showEmptyState() {
        this.friendsList.innerHTML = `
            <div class="text-center text-muted p-3">
                <i class="fas fa-user-friends fa-2x mb-2"></i>
                <p>No tienes amigos agregados</p>
            </div>
        `;
    }

    // Método para establecer el callback de chat
    onChat(callback) {
        this.onChatCallback = callback;
    }

    // Método para actualizar el estado de un amigo específico
    updateFriendStatus(friendId, isOnline) {
        const friendItem = this.friendsList.querySelector(`[data-user-id="${friendId}"]`);
        if (friendItem) {
            const statusDot = friendItem.querySelector('.cw-user-status'); // Cambiado de .user-status a .cw-user-status
            statusDot?.classList.toggle('online', isOnline);
        }
    }

    // Añadir este nuevo método para actualizar todos los estados
    updateAllFriendsStatus() {
        const friendElements = this.container.querySelectorAll('.cw-user-item');
        friendElements.forEach(element => {
            const friendId = parseInt(element.dataset.userId);
            const statusDot = element.querySelector('.cw-user-status');
            if (statusDot) {
                const isOnline = this.onlineUsers.has(friendId);
                statusDot.classList.toggle('online', isOnline);
            }
        });
    }
}