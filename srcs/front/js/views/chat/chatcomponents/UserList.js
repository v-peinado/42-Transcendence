import { webSocketService } from '../../../services/WebSocketService.js';
import { friendService } from '../../../services/FriendService.js';

export class UserList {
    constructor(container) {
        this.container = container;
        this.usersList = container.querySelector('#users-list');
        this.currentFriends = new Set();
        this.sentRequests = new Set(); // Añadir esta línea
        this.requestsContainer = container.querySelector('#requests-container');
        this.friendsContainer = container.querySelector('#friends-container');
        
        // Cargar estado guardado
        this.loadSavedState();
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
        console.log('Actualizando solicitudes enviadas:', requests);
        // Limpiar las solicitudes actuales
        this.sentRequests.clear();
        // Añadir las nuevas solicitudes si existen
        if (Array.isArray(requests)) {
            requests.forEach(req => {
                if (req.to_user_id) {
                    this.sentRequests.add(req.to_user_id);
                }
            });
        }
        this.saveState();
        // Actualizar la vista
        this.updateList(this.lastUserData);
    }

    updateList(data) {
        console.log('Actualizando lista de usuarios:', data);
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
        const hasSentRequest = this.sentRequests.has(userId);

        const userElement = document.createElement('div');
        userElement.className = `cw-user-item ${isFriend ? 'is-friend' : ''}`;
        userElement.dataset.userId = userId;
        
        userElement.innerHTML = `
            <div class="cw-user-info">
                <span class="cw-user-status ${user.is_online ? 'online' : 'offline'}"></span>
                <span class="cw-username">
                    ${user.username}
                    ${isFriend ? '<i class="fas fa-star friend-star" title="Amigo"></i>' : ''}
                </span>
            </div>
            <div class="cw-user-actions">
                <button class="cw-chat-btn" title="Chat privado">
                    <i class="fas fa-comment"></i>
                </button>
                ${!isFriend ? this.createFriendActionButton(user, isFriend, hasSentRequest) : ''}
            </div>
        `;

        this.attachUserEventListeners(userElement, user, isFriend);
        return userElement;
    }

    createFriendActionButton(user, isFriend, hasSentRequest) {
        // Si ya son amigos, no mostrar ningún botón
        if (isFriend) {
            return ''; // Retornamos string vacío si son amigos
        }
        
        // Si hay una solicitud pendiente, mostrar el icono de reloj
        if (hasSentRequest) {
            return `
                <span class="cw-request-pending" title="Solicitud enviada">
                    <i class="fas fa-clock"></i>
                </span>`;
        }
        
        // Si no son amigos y no hay solicitud pendiente, mostrar botón de agregar
        return `
            <button class="cw-friend-add" title="Agregar amigo">
                <i class="fas fa-user-plus"></i>
            </button>`;
    }

    attachUserEventListeners(userElement, user, isFriend) {
        const userId = parseInt(user.id);
        const chatButton = userElement.querySelector('.cw-chat-btn');
        const addButton = userElement.querySelector('.cw-friend-add');

        chatButton?.addEventListener('click', () => {
            this.onChatCallback?.(user.id, user.username);
        });

        // Solo añadir el evento al botón de agregar si existe y no son amigos
        if (addButton && !isFriend) {
            addButton.addEventListener('click', async () => {
                try {
                    addButton.outerHTML = `
                        <span class="cw-request-pending" title="Solicitud enviada">
                            <i class="fas fa-clock"></i>
                        </span>`;
                    await friendService.sendFriendRequest(userId);
                    this.sentRequests.add(userId);
                    this.saveState();
                } catch (error) {
                    console.error('Error al enviar solicitud:', error);
                }
            });
        }
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
                <button class="btn btn-sm btn-outline-success friend-add" 
                    title="Agregar amigo">
                    <i class="fas fa-user-plus"></i>
                </button>`;
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
        console.log('Amistades actualizadas:', friendships);
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
}