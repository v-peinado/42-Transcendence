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
    }

    updateFriendsList(data) {
        this.friendsList.innerHTML = '';
        
        if (!data.friends?.length) {
            this.showEmptyState();
            return;
        }

        data.friends.forEach(friend => {
            const friendElement = this.createFriendElement(friend);
            this.friendsList.appendChild(friendElement);
        });
    }

    createFriendElement(friend) {
        const isFriendUser1 = friend.user1_id === this.currentUserId;
        const friendId = isFriendUser1 ? friend.user2_id : friend.user1_id;
        const friendUsername = isFriendUser1 ? friend.user2__username : friend.user1__username;

        const friendDiv = document.createElement('div');
        friendDiv.className = 'list-group-item friend-item';
        friendDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <span class="user-status ${friend.is_online ? 'user-online' : 'user-offline'}"></span>
                    <span class="ms-2">${friendUsername}</span>
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-primary chat-with-friend" 
                            data-user-id="${friendId}"
                            data-username="${friendUsername}">
                        <i class="fas fa-comment"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-friend" 
                            data-friendship-id="${friend.id}">
                        <i class="fas fa-user-minus"></i>
                    </button>
                </div>
            </div>
        `;

        this.attachFriendEventListeners(friendDiv);
        return friendDiv;
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
        this.pendingRequests.innerHTML = '';
        
        if (!data.pending?.length) return;

        data.pending.forEach(request => {
            const requestElement = this.createRequestElement(request);
            this.pendingRequests.appendChild(requestElement);
        });
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
            const statusDot = friendItem.querySelector('.user-status');
            statusDot?.classList.toggle('user-online', isOnline);
            statusDot?.classList.toggle('user-offline', !isOnline);
        }
    }
}
