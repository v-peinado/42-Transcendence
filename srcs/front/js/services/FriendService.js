import { webSocketService } from './WebSocketService.js';

class FriendService {
    sendFriendRequest(toUserId) {
        webSocketService.send({
            type: 'send_friend_request',
            to_user_id: toUserId
        });
    }

    acceptFriendRequest(requestId) {
        webSocketService.send({
            type: 'accept_friend_request',
            request_id: requestId
        });
    }

    rejectFriendRequest(requestId) {
        return new Promise((resolve) => {
            console.log('Rechazando/Cancelando solicitud:', requestId);
            webSocketService.send({
                type: 'reject_friend_request',
                request_id: requestId
            });
            resolve();
        });
    }

    deleteFriendship(friendshipId) {
        webSocketService.send({
            type: 'delete_friendship',
            friendship_id: friendshipId
        });
    }

    cancelFriendRequest(requestId) {
        return new Promise((resolve) => {
            webSocketService.send({
                type: 'reject_friend_request',
                request_id: requestId
            });
            resolve();
        });
    }
}

export const friendService = new FriendService();