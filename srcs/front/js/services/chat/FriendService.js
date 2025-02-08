class FriendService {
    constructor() {
        this.socket = null;
        this.callbacks = new Map();
    }

    init(websocketService) {
        this.socket = websocketService;
        this.setupHandlers();
    }

    setupHandlers() {
        this.socket.on('friend_list_update', (data) => {
            if (this.callbacks.has('onFriendList')) {
                this.callbacks.get('onFriendList')(data.friends);
            }
        });

        this.socket.on('pending_friend_requests', (data) => {
            if (this.callbacks.has('onPendingRequests')) {
                this.callbacks.get('onPendingRequests')(data.pending);
            }
        });
    }

    sendFriendRequest(userId) {
        this.socket.send({
            type: 'send_friend_request',
            to_user_id: userId
        });
    }

    acceptFriendRequest(requestId) {
        this.socket.send({
            type: 'accept_friend_request',
            request_id: requestId
        });
    }

    rejectFriendRequest(requestId) {
        this.socket.send({
            type: 'reject_friend_request',
            request_id: requestId
        });
    }

    deleteFriendship(friendshipId) {
        this.socket.send({
            type: 'delete_friendship',
            friendship_id: friendshipId
        });
    }

    onFriendList(callback) {
        this.callbacks.set('onFriendList', callback);
    }

    onPendingRequests(callback) {
        this.callbacks.set('onPendingRequests', callback);
    }
}

export const friendService = new FriendService();
