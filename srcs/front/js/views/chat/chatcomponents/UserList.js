import { webSocketService } from '../../../services/WebSocketService.js';
import { friendService } from '../../../services/FriendService.js';
import { blockService } from '../../../services/BlockService.js';
import { ChatUserProfile } from './ChatUserProfile.js';

export class UserList {
    constructor(container) {
        this.container = container;
        this.usersList = container.querySelector('#users-list');
        this.currentFriends = new Set();
        this.sentRequests = new Set(); // Añadir esta línea
        this.requestsContainer = container.querySelector('#requests-container');
        this.friendsContainer = container.querySelector('#friends-container');
        this.onlineUsers = new Set();
        this.userProfile = new ChatUserProfile(container);

        // Suscribirse a eventos de WebSocket
        webSocketService.on('user_online', (data) => this.handleUserStatus(data.user_id, true));
        webSocketService.on('user_offline', (data) => this.handleUserStatus(data.user_id, false));
        webSocketService.on('online_users', (data) => this.handleOnlineUsersList(data.users));
        
        // Cargar estado guardado
        this.loadSavedState();

        // Añadir listener para cambios de estado de bloqueo
        document.addEventListener('block-status-changed', (event) => {
            this.handleBlockStatusChange(event.detail);
        });

        const styles = document.createElement('style');
        styles.textContent = `
            .cw-user-info.disabled {
                opacity: 0.6;
                background-color: #f8f8f8;
                border-left: 3px solid #ff4444;
                padding: 8px;
                pointer-events: none;
            }
            
            .cw-blocked-text {
                color: #ff4444;
                font-size: 0.85em;
                margin-left: 8px;
            }
        `;
        container.appendChild(styles);
    }

    loadSavedState() {
        try {
            const savedFriends = JSON.parse(localStorage.getItem('currentFriends') || '[]');
            this.currentFriends = new Set(savedFriends);
            const savedRequests = JSON.parse(localStorage.getItem('sentRequests') || '[]');
            this.sentRequests = new Set(savedRequests);
        } catch (error) {
            console.error('Error cargando estado guardado:', error);
        }
    }

    saveState() {
        localStorage.setItem('currentFriends', JSON.stringify([...this.currentFriends]));
        localStorage.setItem('sentRequests', JSON.stringify([...this.sentRequests]));
    }

    updateSentRequests(requests) {
        this.sentRequests.clear();
        
        if (Array.isArray(requests)) {
            // Almacenar los IDs de las solicitudes en un Map para acceso rápido
            this.sentRequestsData = new Map();
            
            requests.forEach(req => {
                if (req.to_user_id) {
                    this.sentRequests.add(req.to_user_id);
                    // Guardar el objeto completo de la solicitud
                    this.sentRequestsData.set(parseInt(req.to_user_id), req);
                }
            });
        }
        
        this.saveState();
        this.updateList(this.lastUserData);
    }

    updateList(data) {
        this.lastUserData = data;
        
        const usersList = this.container.querySelector('#widget-users-list');
        if (!usersList) {
            console.error('No se encontró el contenedor de usuarios');
            return;
        }
        
        usersList.innerHTML = '';
        
        // Mostrar estado vacío si no hay usuarios
        if (!data?.users?.length || (data.users.length === 1 && data.users[0].id === parseInt(localStorage.getItem('user_id')))) {
            usersList.innerHTML = `
                <div class="cw-empty-state">
                    <i class="fas fa-users-slash"></i>
                    <p>No hay usuarios conectados</p>
                    <small>Espera a que alguien se conecte</small>
                </div>
            `;
            return;
        }

        // Filtrar el usuario actual
        const currentUserId = parseInt(localStorage.getItem('user_id'));
        const otherUsers = data.users.filter(user => user.id !== currentUserId);

        // Usar createUserElement para cada usuario
        otherUsers.forEach(user => {
            const userElement = this.createUserElement(user);
            usersList.appendChild(userElement);
        });
    }

    showEmptyState() {
        this.usersList.innerHTML = `
            <div class="text-center text-muted p-3">
                <i class="fas fa-users-slash fa-2x mb-2"></i>
                <p>No hay otros usuarios conectados</p>
                <small>Espera a que alguien se conecte</small>
            </div>
        `;
    }

    createUserElement(user) {
        const userId = parseInt(user.id);
        const isFriend = this.currentFriends.has(userId);
        const isBlocked = blockService.hasBlockedUser(userId);
        const isBlockedByUser = blockService.isBlockedByUser(userId);
        
        const userElement = document.createElement('div');
        userElement.className = 'cw-user-item';
        userElement.dataset.userId = userId;

        // Mostrar como deshabilitado si el usuario nos ha bloqueado
        if (isBlockedByUser) {
            userElement.innerHTML = `
                <div class="cw-user-info disabled">
                    <span class="cw-username">
                        ${user.username}
                        <i class="fas fa-lock text-danger"></i>
                        <span class="text-muted">(Te ha bloqueado)</span>
                    </span>
                </div>
            `;
            userElement.style.pointerEvents = 'none';
            userElement.style.opacity = '0.6';
            userElement.style.backgroundColor = '#f5f5f5';
            return userElement;
        }

        const userInfo = document.createElement('div');
        userInfo.className = 'cw-user-info';
        userInfo.innerHTML = `
            <span class="cw-user-status online"></span>
            <span class="cw-username">${user.username}</span>
            ${isFriend ? '<i class="fas fa-star friend-star"></i>' : ''}
            ${isBlocked ? '<i class="fas fa-ban text-danger"></i>' : ''}
        `;
        
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'cw-user-actions';
        actionsDiv.innerHTML = this.createUserActions(user);

        userElement.appendChild(userInfo);
        userElement.appendChild(actionsDiv);

        this.attachUserEventListeners(userElement, user);
        return userElement;
    }

    createUserActions(user) {
        // En lugar de crear un elemento DOM, vamos a devolver un string template
        const userId = parseInt(user.id);
        const isFriend = this.currentFriends.has(userId);
        const hasSentRequest = this.sentRequests.has(userId);
        const isBlocked = blockService.hasBlockedUser(userId);

        return `
            <div class="cw-user-actions-group">
                <button class="cw-profile-btn" title="Ver perfil">
                    <i class="fas fa-user"></i>
                </button>
                ${!isBlocked ? `
                    <button class="cw-chat-btn" title="Chat privado">
                        <i class="fas fa-comment"></i>
                    </button>
                    ${!isFriend ? `
                        ${!hasSentRequest ? `
                            <button class="cw-friend-add" title="Agregar amigo">
                                <i class="fas fa-user-plus"></i>
                            </button>
                        ` : `
                            <button class="cw-cancel-request" 
                                title="Cancelar solicitud" 
                                data-request-id="${this.sentRequestsData?.get(userId)?.request_id}">
                                <i class="fas fa-clock"></i>
                            </button>
                        `}
                    ` : ''}
                    <button class="cw-block-btn" title="Bloquear usuario">
                        <i class="fas fa-ban"></i>
                    </button>
                ` : `
                    <button class="cw-unblock-btn" title="Desbloquear usuario">
                        <i class="fas fa-unlock"></i>
                    </button>
                `}
            </div>
        `;
    }

    createFriendButtons(user) {
        const userId = parseInt(user.id);
        const isFriend = this.currentFriends.has(userId);
        const hasSentRequest = this.sentRequests.has(userId);

        if (isFriend) {
            return `
                <button class="cw-friend-remove" title="Eliminar amigo">
                    <i class="fas fa-user-minus"></i>
                </button>`;
        } else if (hasSentRequest) {
            return `
                <span class="cw-request-pending" title="Solicitud enviada">
                    <i class="fas fa-clock"></i>
                </span>`;
        } else {
            return `
                <button class="cw-friend-add" title="Agregar amigo">
                    <i class="fas fa-user-plus"></i>
                </button>`;
        }
    }

    attachUserEventListeners(userElement, user) {
        const userId = parseInt(user.id);
        
        const profileBtn = userElement.querySelector('.cw-profile-btn');
        if (profileBtn) {
            profileBtn.addEventListener('click', async (e) => {
                const data = await this.userProfile.fetchStats(userId);
                if (data) {
                    this.userProfile.showModal(data, e.currentTarget);
                }
            });
        }

        // Manejar botón de bloqueo
        const blockBtn = userElement.querySelector('.cw-block-btn');
        if (blockBtn) {
            blockBtn.addEventListener('click', () => {
                blockBtn.style.display = 'none';
                blockService.blockUser(userId);
            }, { once: true });
        }

        // Manejar botón de desbloqueo
        const unblockBtn = userElement.querySelector('.cw-unblock-btn');
        if (unblockBtn) {
            unblockBtn.addEventListener('click', () => {
                unblockBtn.style.display = 'none';
                blockService.unblockUser(userId);
            }, { once: true });
        }

        // Chat button
        const chatButton = userElement.querySelector('.cw-chat-btn');
        if (chatButton) {
            chatButton.addEventListener('click', () => {
                if (this.onChatClick) {
                    this.onChatClick(userId, user.username);
                }
            });
        }

        // Friend buttons
        const addFriendBtn = userElement.querySelector('.cw-friend-add');
        const removeFriendBtn = userElement.querySelector('.cw-friend-remove');

        if (addFriendBtn) {
            addFriendBtn.addEventListener('click', async () => {
                await friendService.sendFriendRequest(userId);
                this.sentRequests.add(userId);
                this.saveState();
                this.updateList(this.lastUserData);
            });
        }

        if (removeFriendBtn) {
            removeFriendBtn.addEventListener('click', () => {
                // Obtener la amistad directamente de lastUserData.friends
                const friendship = this.lastUserData.friends.find(f => 
                    (parseInt(f.user1_id) === userId || parseInt(f.user2_id) === userId)
                );
                
                if (friendship) {
                    friendService.deleteFriendship(friendship.id);
                    
                    // Actualizar UI y estado
                    removeFriendBtn.closest('.cw-user-item').remove();
                    this.currentFriends.delete(userId);
                    this.saveState();
                    
                    // Forzar actualización de las listas
                    webSocketService.send({ type: 'get_friend_list' });
                } else {
                    console.error('No se encontró la amistad para:', userId);
                }
            });
        }

        // Modificar el manejador del botón de cancelar solicitud
        const cancelRequestBtn = userElement.querySelector('.cw-cancel-request');
        if (cancelRequestBtn) {
            cancelRequestBtn.addEventListener('click', async () => {
                const requestId = cancelRequestBtn.dataset.requestId;
                if (requestId) {
                    
                    // Enviar la cancelación
                    webSocketService.send({
                        type: 'reject_friend_request',
                        request_id: requestId
                    });

                    // Actualizar estado local
                    this.sentRequests.delete(user.id);
                    this.sentRequestsData?.delete(user.id);
                    this.saveState();

                    // Actualizar UI
                    const actionsContainer = userElement.querySelector('.cw-user-actions');
                    actionsContainer.innerHTML = this.createUserActions(user);
                    this.attachUserEventListeners(userElement, user);
                } else {
                    console.error('No se encontró el ID de la solicitud en el botón');
                }
            });
        }
    }

    async findSentRequest(userId) {
        return new Promise((resolve) => {
            const handler = (event) => {
                if (typeof event === 'object') {
                    const pending = event.pending || [];
                    const request = pending.find(req => 
                        parseInt(req.to_user_id) === parseInt(userId)
                    );
                    
                    if (request) {
                        webSocketService.off('sent_friend_requests', handler);
                        resolve(request);
                    }
                }
            };

            // Registrar el listener y enviar la solicitud
            webSocketService.on('sent_friend_requests', handler);
            webSocketService.send({ type: 'get_sent_requests' });

            // Timeout de seguridad
            setTimeout(() => {
                webSocketService.off('sent_friend_requests', handler);
                resolve(null);
            }, 3000);
        });
    }

    updateUserBlockState(userElement, isBlocked) {
        // Actualizar clase
        userElement.classList.toggle('is-blocked', isBlocked);
        
        // Actualizar icono
        const username = userElement.querySelector('.cw-username');
        const existingIcon = username.querySelector('.fas.fa-ban');
        
        if (isBlocked && !existingIcon) {
            username.insertAdjacentHTML('beforeend', 
                '<i class="fas fa-ban text-danger" title="Bloqueado por ti"></i>');
        } else if (!isBlocked && existingIcon) {
            existingIcon.remove();
        }
        
        // Actualizar botones
        const actionsContainer = userElement.querySelector('.cw-user-actions');
        const userId = parseInt(userElement.dataset.userId);
        const user = this.lastUserData.users.find(u => u.id === userId);
        
        if (user) {
            actionsContainer.innerHTML = this.createUserActions(user, isBlocked ? 'blocked' : null);
            this.attachUserEventListeners(userElement, user);
        }
    }

    updateButtonState(userElement, isBlocked) {
        const userId = parseInt(userElement.dataset.userId);
        const user = this.lastUserData.users.find(u => u.id === userId);
        
        if (!user) return;

        // Actualizar el estado visual inmediatamente
        userElement.classList.toggle('is-blocked', isBlocked);
        
        // Actualizar los iconos
        const usernameSpan = userElement.querySelector('.cw-username');
        const blockIcon = usernameSpan.querySelector('.fas.fa-ban');
        
        if (isBlocked && !blockIcon) {
            usernameSpan.insertAdjacentHTML('beforeend', 
                '<i class="fas fa-ban text-danger" title="Bloqueado por ti"></i>'
            );
        } else if (!isBlocked && blockIcon) {
            blockIcon.remove();
        }

        // Actualizar los botones
        const actionsContainer = userElement.querySelector('.cw-user-actions');
        actionsContainer.innerHTML = this.createUserActions(user, isBlocked ? 'blocked' : null);
        
        // Re-adjuntar event listeners
        this.attachUserEventListeners(userElement, user);
    }

    getBlockedUserHTML(user) {
        return `
            <div class="cw-user-info">
                <span class="cw-user-status ${user.is_online ? 'online' : 'offline'}"></span>
                <span class="cw-username">
                    ${user.username}
                    <i class="fas fa-ban text-danger" title="Bloqueado por ti"></i>
                </span>
            </div>
            <div class="cw-user-actions">
                <div class="cw-user-actions-group">
                    <button class="cw-unblock-btn" title="Desbloquear usuario">
                        <i class="fas fa-unlock"></i>
                    </button>
                </div>
            </div>`;
    }

    getUnblockedUserHTML(user) {
        const isFriend = this.currentFriends.has(parseInt(user.id));
        return `
            <div class="cw-user-info">
                <span class="cw-user-status ${user.is_online ? 'online' : 'offline'}"></span>
                <span class="cw-username">
                    ${user.username}
                    ${isFriend ? '<i class="fas fa-star friend-star" title="Amigo"></i>' : ''}
                </span>
            </div>
            <div class="cw-user-actions">
                <div class="cw-user-actions-group">
                    <button class="cw-chat-btn" title="Chat privado">
                        <i class="fas fa-comment"></i>
                    </button>
                    ${this.createFriendButtons(user)}
                    <button class="cw-block-btn" title="Bloquear usuario">
                        <i class="fas fa-ban"></i>
                    </button>
                </div>
            </div>`;
    }

    // Añadir método para manejar respuestas a solicitudes
    handleFriendRequestResponse(userId, accepted) {
        // Buscar el elemento de solicitud pendiente
        const userElement = this.container.querySelector(`[data-user-id="${userId}"]`);
        if (!userElement) return;

        const pendingElement = userElement.querySelector('.cw-request-pending');
        if (pendingElement) {
            if (accepted) {
                // Si fue aceptada, mostrar botón de eliminar amigo
                pendingElement.outerHTML = `
                    <button class="cw-friend-remove" title="Eliminar amigo">
                        <i class="fas fa-user-minus"></i>
                    </button>`;
            } else {
                // Si fue rechazada, volver a mostrar el botón de agregar
                pendingElement.outerHTML = `
                    <button class="cw-friend-add" title="Agregar amigo">
                        <i class="fas fa-user-plus"></i>
                    </button>`;
            }
            // Actualizar el conjunto de solicitudes enviadas
            this.sentRequests.delete(userId);
            this.saveState();
        }
    }

    createChatButton(user) {
        const isBlocked = user.is_blocked || user.has_blocked_you;
        return `
            <button class="btn btn-sm btn-outline-primary chat-btn" ${isBlocked ? 'disabled' : ''} 
                title="Chat privado">
                <i class="fas fa-comment-dots"></i>
            </button>
        `;
    }

    createActionButtons(user) {
        const userId = parseInt(user.id);
        const isFriend = this.currentFriends.has(userId);
        const hasSentRequest = this.sentRequests.has(userId);
        const isBlocked = blockService.isBlocked(userId);

        if (isFriend) {
            return `
                <div class="btn-group">
                    <button class="btn btn-sm btn-outline-danger friend-remove" 
                        title="Eliminar amigo">
                        <i class="fas fa-user-minus"></i>
                    </button>
                </div>`;
        } else if (hasSentRequest) {
            return `
                <span class="badge bg-secondary text-light" style="min-width: 120px;">
                    <i class="fas fa-clock me-1"></i> Solicitud enviada
                </span>`;
        } else {
            return `
                <div class="cw-user-actions">
                    ${!isBlocked ? `
                        <button class="cw-chat-btn" title="Chat privado">
                            <i class="fas fa-comment"></i>
                        </button>
                        <button class="cw-block-btn" title="Bloquear usuario">
                            <i class="fas fa-ban"></i>
                        </button>
                    ` : `
                        <button class="cw-unblock-btn" title="Desbloquear usuario">
                            <i class="fas fa-unlock"></i>
                        </button>
                    `}
                </div>
            `;
        }
    }

    attachEventListeners(userDiv, user) {
        const userId = parseInt(user.id);

        // Chat button listener
        const chatBtn = userDiv.querySelector('.chat-btn');
        if (chatBtn && !chatBtn.disabled) {
            chatBtn.addEventListener('click', () => {
                this.onChatClick?.(userId, user.username);
            });
        }

        // Friend action listeners
        const addBtn = userDiv.querySelector('.friend-add');
        if (addBtn) {
            addBtn.addEventListener('click', async () => {
                addBtn.outerHTML = '<span class="badge bg-info" style="min-width: 120px;">Solicitud enviada</span>';
                await friendService.sendFriendRequest(userId);
            });
        }

        const removeBtn = userDiv.querySelector('.friend-remove');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                const friendship = this.currentFriendships?.find(f => 
                    (f.user1_id === userId || f.user2_id === userId)
                );
                if (friendship) {
                    friendService.deleteFriendship(friendship.id);
                }
            });
        }
    }

    setCurrentFriends(friends) {
        this.currentFriends = new Set(friends);
        this.saveState();
        // Forzar actualización de la UI
        if (this.lastUserData) {
            this.updateList(this.lastUserData);
        }
    }

    setCurrentFriendships(friendships) {
        this.currentFriendships = friendships;
    }

    // Método para establecer el callback de chat
    onUserChat(callback) {
        this.onChatClick = callback;
    }

    // Método para actualizar el estado de un usuario específico
    updateUserStatus(userId, isOnline) {
        const userItem = this.usersList.querySelector(`[data-user-id="${userId}"]`);
        if (userItem) {
            const statusDot = userItem.querySelector('.user-status');
            statusDot?.classList.toggle('user-online', isOnline);
            statusDot?.classList.toggle('user-offline', !isOnline);
        }
    }

    handleTabChange(tab) {
        switch(tab) {
            case 'users':
                this.updateList(this.lastUserData);
                break;
            case 'requests':
                break;
            case 'friends':
                break;
        }
    }

    handleBlockStatusChange(detail) {
        if (!detail?.userId) return;

        const userElement = this.container.querySelector(`[data-user-id="${detail.userId}"]`);
        if (!userElement) return;

        // Actualizar UI directamente
        const user = this.lastUserData.users.find(u => u.id === detail.userId);
        if (user) {
            userElement.innerHTML = detail.isBlocked ? 
                this.getBlockedUserHTML(user) : 
                this.getUnblockedUserHTML(user);
                
            // Re-adjuntar listeners
            this.attachUserEventListeners(userElement, user);
        }
    }

    handleUserStatus(userId, isOnline) {
        if (isOnline) {
            this.onlineUsers.add(userId);
        } else {
            this.onlineUsers.delete(userId);
        }
        this.updateUserStatus(userId, isOnline);
    }

    handleOnlineUsersList(users) {
        // Limpiar lista actual
        this.onlineUsers.clear();
        
        // Añadir nuevos usuarios online
        users.forEach(userId => this.onlineUsers.add(userId));
        
        // Actualizar todos los indicadores
        this.updateAllStatuses();
    }

    updateUserStatus(userId, isOnline) {
        const userElement = this.container.querySelector(`[data-user-id="${userId}"]`);
        if (userElement) {
            const statusDot = userElement.querySelector('.cw-user-status');
            if (statusDot) {
                statusDot.classList.toggle('online', isOnline);
            }
        }
    }

    updateAllStatuses() {
        this.container.querySelectorAll('.cw-user-item').forEach(userElement => {
            const userId = parseInt(userElement.dataset.userId);
            const statusDot = userElement.querySelector('.cw-user-status');
            if (statusDot) {
                statusDot.classList.toggle('online', this.onlineUsers.has(userId));
            }
        });
    }

    isUserOnline(userId) {
        return this.onlineUsers.has(userId);
    }
}