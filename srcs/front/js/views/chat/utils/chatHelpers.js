export const chatHelpers = {
    formatMessage(message) {
        return {
            text: message.trim(),
            timestamp: new Date().toISOString()
        };
    },

    createChannelName(userId1, userId2) {
        const minId = Math.min(userId1, userId2);
        const maxId = Math.max(userId1, userId2);
        return `dm_${minId}_${maxId}`;
    },

    getCurrentUserId() {
        return parseInt(localStorage.getItem('user_id'));
    },

    isCurrentUser(userId) {
        return userId === this.getCurrentUserId();
    },

    limitMessagesInContainer(container, maxMessages = 100) {
        const messages = container.children;
        while (messages.length > maxMessages) {
            container.removeChild(messages[0]);
        }
    },

    scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    },
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
};
