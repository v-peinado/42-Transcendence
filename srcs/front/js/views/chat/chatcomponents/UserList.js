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
    }

    updateSentRequests(requests) {
        this.sentRequests = new Set(requests.map(req => req.to_user_id));
        this.updateList(this.lastUserData); // Actualizar la vista con los datos almacenados
    }

    updateList(data) {
        this.lastUserData = data;
        this.usersList.innerHTML = '';
        
        // Mostrar estado vacío si no hay usuarios o solo está el usuario actual
        if (!data.users?.length || data.users.length === 1) {
            this.showEmptyState();
            return;
        }
        
        data.users.forEach(user => {
            if (user.id === parseInt(localStorage.getItem('user_id'))) return;

            const userDiv = this.createUserElement(user);
            this.usersList.appendChild(userDiv);
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
        const userDiv = document.createElement('div');
        userDiv.classList.add('list-group-item', 'user-item', 'py-2');
        userDiv.setAttribute('data-user-id', user.id);
        userDiv.setAttribute('data-username', user.username);

        const actionButtons = this.createActionButtons(user);
        
        userDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="user-info d-flex align-items-center">
                    <span class="user-status ${user.is_online ? 'user-online' : 'user-offline'} me-2"></span>
                    <span class="username">${user.username}</span>
                    ${user.has_blocked_you ? 
                        '<span class="badge bg-danger blocked-by-badge ms-2"><i class="fas fa-ban"></i> Bloqueado</span>' 
                        : ''}
                </div>
                <div class="btn-group">
                    ${this.createChatButton(user)}
                    ${actionButtons}
                </div>
            </div>`;

        this.attachEventListeners(userDiv, user);
        return userDiv;
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
                // La lista de solicitudes se actualiza automáticamente
                break;
            case 'friends':
                // La lista de amigos se actualiza automáticamente
                break;
        }
    }
}
