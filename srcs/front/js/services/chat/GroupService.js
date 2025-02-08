class GroupService {
    constructor() {
        this.socket = null;
        this.callbacks = new Map();
    }

    init(websocketService) {
        this.socket = websocketService;
        this.setupHandlers();
    }

    setupHandlers() {
        this.socket.on('user_groups', (data) => {
            if (this.callbacks.has('onGroupList')) {
                this.callbacks.get('onGroupList')(data.groups);
            }
        });
    }

    createGroup(groupName) {
        this.socket.send({
            type: 'create_group',
            group_name: groupName
        });
    }

    addUserToGroup(userId, groupId) {
        this.socket.send({
            type: 'add_user_to_group',
            group_id: groupId,
            user_id: userId
        });
    }

    leaveGroup(groupId, groupName) {
        this.socket.send({
            type: 'leave_group',
            id: groupId,
            groupname: groupName,
            userId: localStorage.getItem('user_id')
        });
    }

    onGroupList(callback) {
        this.callbacks.set('onGroupList', callback);
    }
}

export const groupService = new GroupService();
