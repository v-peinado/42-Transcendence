import { webSocketService } from './WebSocketService.js';

class BlockService {
    constructor() {
        this.blockedUsers = new Set();
        this.blockedByUsers = new Set();
        this.loadBlockedState();
    }

    loadBlockedState() {
        try {
            const state = JSON.parse(localStorage.getItem('blockedState') || '{}');
            this.blockedUsers = new Set(state.blocking || []);
            this.blockedByUsers = new Set(state.blockedBy || []);
        } catch (error) {
            console.error('Error loading blocked state:', error);
        }
    }

    saveBlockedState() {
        const state = {
            blocking: Array.from(this.blockedUsers),
            blockedBy: Array.from(this.blockedByUsers)
        };
        localStorage.setItem('blockedState', JSON.stringify(state));
    }

    blockUser(userId) {
        this.blockedUsers.add(userId);
        this.saveBlockedState();
        
        // Volver al mensaje simple de bloqueo
        webSocketService.send({
            type: 'block_user',
            user_id: userId
        });
        
        console.log('Usuario bloqueado:', userId);
        this.notifyBlockUpdate(userId, 'blocked');
    }

    unblockUser(userId) {
        this.blockedUsers.delete(userId);
        this.saveBlockedState();
        webSocketService.send({
            type: 'block_user',
            user_id: userId
        });
        console.log('Usuario desbloqueado:', userId); // Debug
        this.notifyBlockUpdate(userId, 'unblocked');
    }

    handleBlockedUsers(data) {
        if (data.type === 'unblocked') {
            this.blockedUsers.delete(data.user_id);
            this.blockedByUsers.delete(data.user_id);
        } else if (data.type === 'blocked_by') {
            // Nuevo: cuando alguien nos bloquea
            this.blockedByUsers.add(data.user_id);
            console.log('Has sido bloqueado por:', data.user_id);
        } else {
            // Actualizar listas de bloqueados
            this.blockedUsers = new Set(data.blocking?.map(user => user.id) || []);
            this.blockedByUsers = new Set(data.blocked_by?.map(user => user.id) || []);
        }
        this.saveBlockedState();
        this.notifyBlockUpdate();
    }

    hasBlockedUser(userId) {
        return this.blockedUsers.has(userId);
    }

    isBlockedByUser(userId) {
        return this.blockedByUsers.has(userId);
    }

    isBlocked(userId) {
        return this.hasBlockedUser(userId) || this.isBlockedByUser(userId);
    }

    getBlockReason(userId) {
        if (this.hasBlockedUser(userId)) return 'blocked';
        if (this.isBlockedByUser(userId)) return 'blockedBy';
        return null;
    }

    notifyBlockUpdate(userId, action) {
        document.dispatchEvent(new CustomEvent('block-status-changed', {
            detail: {
                userId,
                action,
                isBlocked: this.hasBlockedUser(userId),
                isBlockedBy: this.isBlockedByUser(userId)
            }
        }));
    }
}

export const blockService = new BlockService();
