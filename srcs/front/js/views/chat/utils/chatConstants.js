export const CHAT_CONSTANTS = {
    EVENTS: {
        CHAT_MESSAGE: 'chat_message',
        PRIVATE_CHANNELS: 'private_channels',
        USER_LIST: 'user_list',
        USER_STATUS: 'user_status',
        FRIEND_LIST_UPDATE: 'friend_list_update',
        FRIEND_REQUEST_SENT: 'friend_request_sent',
        FRIEND_REQUEST_RECEIVED: 'friend_request_received',
        FRIEND_REQUEST_ACCEPTED: 'friend_request_accepted',
        FRIENDSHIP_DELETED: 'friendship_deleted',
        PENDING_REQUESTS: 'pending_friend_requests',
        ERROR: 'error'
    },

    ACTIONS: {
        REQUEST_FRIEND_LIST: 'request_friend_list',
        REQUEST_USER_LIST: 'request_user_list',
        REQUEST_PENDING_REQUESTS: 'request_pending_requests',
        SEND_FRIEND_REQUEST: 'send_friend_request',
        ACCEPT_FRIEND_REQUEST: 'accept_friend_request',
        REJECT_FRIEND_REQUEST: 'reject_friend_request',
        DELETE_FRIENDSHIP: 'delete_friendship',
        CREATE_PRIVATE_CHANNEL: 'create_private_channel'
    },

    UI: {
        MAX_MESSAGES: 100,
        MESSAGE_DELAY: 100,
        REQUEST_DELAY: 500,
        ANIMATION_DURATION: 300
    },

    CHANNELS: {
        GENERAL: 'chat_general',
        PRIVATE_PREFIX: 'dm_'
    },

    STATUS: {
        ONLINE: 'user-online',
        OFFLINE: 'user-offline'
    }
};
