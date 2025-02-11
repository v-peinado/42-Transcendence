import { webSocketService } from '../../services/WebSocketService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import AuthService from '../../services/AuthService.js';
import { friendService } from '../../services/FriendService.js';

let isInitialLoad = true;

export async function ChatView() {
    // Primero verificar autenticación
    if (localStorage.getItem('isAuthenticated') !== 'true') {
        console.log('Usuario no autenticado, redirigiendo a login');
        window.location.href = '/login';
        return;
    }

    // Intentar obtener el perfil primero
    try {
        const profile = await AuthService.getUserProfile();
        console.log('Perfil obtenido:', profile);
        
        if (profile && profile.id) {
            console.log('Guardando ID de usuario:', profile.id);
            localStorage.setItem('user_id', profile.id.toString());
        } else {
            console.error('No se pudo obtener el ID de usuario del perfil:', profile);
        }
    } catch (error) {
        console.error('Error al obtener el perfil:', error);
    }

    const userId = localStorage.getItem('user_id');
    console.log('Chat inicializado con user_id:', {
        id: userId,
        isValid: !isNaN(parseInt(userId)),
        rawValue: localStorage.getItem('user_id'),
        username: localStorage.getItem('username'),
        isAuthenticated: localStorage.getItem('isAuthenticated')
    });

    const appDiv = document.getElementById('app');
    
    const userInfo = {
        username: localStorage.getItem('username'),
    };
    appDiv.innerHTML = await getNavbarHTML(true, userInfo);

    const container = document.createElement('div');
    
    const isFullscreenChat = window.location.pathname === '/chat';
    container.className = `chat-container ${isFullscreenChat ? 'chat-fullscreen' : 'chat-widget'}`;
    
    const response = await fetch('/views/chat/ChatView.html');
    const html = await response.text();
    container.innerHTML = html;

    //esto es para cuando añada game, es un collapse 
    if (!isFullscreenChat) {
        const chatHeader = container.querySelector('#chatHeader');
        if (chatHeader) {
            chatHeader.addEventListener('click', () => {
                container.classList.toggle('collapsed');
                // Guardar estado en localStorage
                localStorage.setItem('chatCollapsed', container.classList.contains('collapsed'));
            });

            // Restaurar estado anterior
            const wasCollapsed = localStorage.getItem('chatCollapsed') === 'true';
            if (wasCollapsed) {
                container.classList.add('collapsed');
            }
        }
    }

    // Referencias a elementos del DOM
    const messagesContainer = container.querySelector('#messages');
    const usersList = container.querySelector('#users-list');
    const messageInput = container.querySelector('#message-input');
    const sendButton = container.querySelector('#send-button');
    const chatTabs = container.querySelector('#chat-tabs');
    const chatContainers = container.querySelector('#chat-containers');
    
    // Referencias adicionales para chat privado
    const privateChatsContainer = container.querySelector('.private-chats-list');
    const activePrivateChat = container.querySelector('#active-private-chat');
    const privateChatUsername = container.querySelector('#private-chat-username');
    const privateMessages = container.querySelector('#private-messages');
    const privateMessageInput = container.querySelector('#private-message-input');
    const privateSendButton = container.querySelector('#private-send-button');

    let currentPrivateChat = null; 
    let messageHistory = new Map(); 

    // Mantener un conjunto de amigos actual
    let currentFriends = new Set();

    // Función para añadir mensaje al chat
    function addMessage(data) {
        const isPrivateMessage = data.channel_name?.startsWith('dm_');
        const isForCurrentChat = isPrivateMessage ? 
            data.channel_name === currentPrivateChat : 
            !data.channel_name?.startsWith('dm_');

        // Si es un mensaje privado y no es del chat actual ni es nuestro propio mensaje
        if (isPrivateMessage && !isForCurrentChat && data.user_id !== parseInt(localStorage.getItem('user_id'))) {
            console.log('Intentando mostrar notificación para mensaje de:', {
                userId: data.user_id,
                username: data.username,
                channelName: data.channel_name
            });

            // Buscar el elemento del usuario usando el atributo data-user-id
            const userItem = document.querySelector(`.user-item[data-user-id="${data.user_id}"]`);
            if (userItem) {
                console.log('Usuario encontrado en la lista, añadiendo notificación');
                if (!userItem.querySelector('.notification-dot')) {
                    const dot = document.createElement('span');
                    dot.className = 'notification-dot';
                    userItem.appendChild(dot);
                }
            } else {
                console.log('Usuario no encontrado en la lista');
            }
        }

        // Solo mostrar el mensaje si es para el chat actual
        if (isForCurrentChat) {
            const targetContainer = isPrivateMessage ? privateMessages : messagesContainer;
            
            console.log('Mensaje recibido:', {
                tipo: data.type,
                usuario_id: data.user_id,
                usuario_nombre: data.username,
                mensaje: data.message,
                canal: data.channel_name
            });

            const messageDiv = document.createElement('div');
            messageDiv.classList.add('msg');
            messageDiv.classList.add(data.user_id === parseInt(localStorage.getItem('user_id')) ? 'my-msg' : 'other-msg');
            
            const username = data.username;
            const message = data.message;
            messageDiv.innerHTML = `
                <small class="d-block mb-1 text-muted">${username}</small>
                <span>${message}</span>
            `;

            targetContainer.appendChild(messageDiv);
            targetContainer.scrollTop = targetContainer.scrollHeight;
        }
    }

    // Función para manejar mensajes históricos
    function handleHistoricalMessages(data) {
        const isPrivateMessage = data.channel_name?.startsWith('dm_');
        
        // Almacenar mensaje en el historial
        if (isPrivateMessage) {
            if (!messageHistory.has(data.channel_name)) {
                messageHistory.set(data.channel_name, []);
            }
            // Insertar en orden por timestamp
            const messages = messageHistory.get(data.channel_name);
            const timestamp = new Date(data.timestamp);
            messages.push({...data, timestamp});
            messages.sort((a, b) => a.timestamp - b.timestamp);
        }

        // Si es el chat actual, mostrar el mensaje
        if (data.channel_name === currentPrivateChat || (!isPrivateMessage && data.channel_name === 'chat_general')) {
            addMessage(data);
        }
    }

    // Función para abrir chat privado
    function openPrivateChat(userId, username) {
        // Obtener userID y asegurarnos de que sea un número válido
        const currentUserId = parseInt(localStorage.getItem('user_id'));
        
        if (isNaN(currentUserId)) {
            console.error('Error: user_id no válido en localStorage:', localStorage.getItem('user_id'));
            return;
        }

        const minId = Math.min(currentUserId, userId);
        const maxId = Math.max(currentUserId, userId);
        
        console.log('Iniciando chat privado:', { 
            currentUserId,
            otherUserId: userId,
            minId, 
            maxId, 
            username 
        });
        
        // Crear canal solo si tenemos IDs válidos
        if (!isNaN(minId) && !isNaN(maxId)) {
            webSocketService.send({
                type: 'create_private_channel',
                user1_id: minId,
                user2_id: maxId
            });

            // Cambiar a la pestaña de privados
            const privateTab = chatTabs.querySelector('[data-tab="private"]');
            if (privateTab) {
                privateTab.click();
            }

            // Mostrar el chat privado con el usuario seleccionado
            showPrivateChat(`dm_${minId}_${maxId}`, username);
        }

        // Eliminar la notificación al abrir el chat
        const userItem = document.querySelector(`.user-item[data-user-id="${userId}"]`);
        if (userItem) {
            const dot = userItem.querySelector('.notification-dot');
            if (dot) dot.remove();
        }
    }

    // Modificar la función updateUsersList
    function updateUsersList(data) {
        console.log('DEBUG - Estado de usuarios:', {
            users: data.users.map(u => ({
                username: u.username,
                id: u.id,
                has_sent_request: Boolean(u.friend_request_sent), // Convertir explícitamente a booleano
                sent_to: u.request_sent_to,
                received_from: u.request_received_from
            }))
        });

        usersList.innerHTML = '';
        
        data.users.forEach(user => {
            const currentUserId = parseInt(localStorage.getItem('user_id'));
            const userId = parseInt(user.id);
            
            if (userId === currentUserId) return;

            const userDiv = document.createElement('div');
            userDiv.classList.add('list-group-item', 'user-item');
            userDiv.setAttribute('data-user-id', user.id);
            userDiv.setAttribute('data-username', user.username);
            
            const isFriend = currentFriends.has(userId);
            // Simplificar la verificación de solicitud enviada
            const hasSentRequest = Boolean(user.friend_request_sent);

            let actionButtons = '';
            if (isFriend) {
                actionButtons = `
                    <div class="btn-group">
                        <button class="btn btn-sm btn-danger friend-remove">
                            <i class="fas fa-user-minus"></i>
                        </button>
                    </div>`;
            } else if (hasSentRequest) {
                actionButtons = '<span class="badge bg-info" style="min-width: 120px;">Solicitud enviada</span>';
            } else {
                const addBtn = document.createElement('button');
                addBtn.className = 'btn btn-sm btn-success friend-add';
                addBtn.innerHTML = '<i class="fas fa-user-plus"></i>';
                
                // Agregar evento click
                addBtn.addEventListener('click', async () => {
                    // Cambiar inmediatamente a "Solicitud enviada"
                    addBtn.outerHTML = '<span class="badge bg-info" style="min-width: 120px;">Solicitud enviada</span>';
                    
                    // Enviar la solicitud
                    try {
                        await friendService.sendFriendRequest(userId);
                    } catch (error) {
                        // Si hay error porque ya existe la solicitud, mantener el estado "Solicitud enviada"
                        if (error.message !== 'Friend request already exists') {
                            // Solo revertir si es otro tipo de error
                            addBtn.outerHTML = '<button class="btn btn-sm btn-success friend-add"><i class="fas fa-user-plus"></i></button>';
                        }
                    }
                });
                
                actionButtons = addBtn.outerHTML;
            }

            userDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div class="user-info">
                        <span class="user-status ${user.is_online ? 'user-online' : 'user-offline'}"></span>
                        ${user.username}
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-sm btn-primary chat-btn">
                            <i class="fas fa-comment"></i>
                        </button>
                        ${actionButtons}
                    </div>
                </div>`;

            // Event listeners
            userDiv.querySelector('.chat-btn').addEventListener('click', () => {
                openPrivateChat(userId, user.username);
            });

            // En la función donde agregamos los event listeners para el botón de agregar amigo
            if (!hasSentRequest && !isFriend) {
                const addBtn = userDiv.querySelector('.friend-add');
                if (addBtn) {
                    addBtn.addEventListener('click', () => {
                        // Actualizar UI inmediatamente antes de enviar la solicitud
                        const buttonContainer = addBtn.parentElement;
                        buttonContainer.innerHTML = '<span class="badge bg-info" style="min-width: 120px;">Solicitud enviada</span>';
                        
                        // Enviar la solicitud
                        friendService.sendFriendRequest(userId);
                        
                        // Marcar como enviada aunque obtengamos error
                        user.friend_request_sent = true;
                    });
                }
            }

            if (isFriend) {
                const removeBtn = userDiv.querySelector('.friend-remove');
                if (removeBtn) {
                    removeBtn.addEventListener('click', () => {
                        const friendship = data.friends?.find(f => 
                            (f.user1_id === userId && f.user2_id === currentUserId) || 
                            (f.user1_id === currentUserId && f.user2_id === userId)
                        );
                        if (friendship) {
                            friendService.deleteFriendship(friendship.id);
                        }
                    });
                }
            }

            usersList.appendChild(userDiv);
        });
    }

    function createUserElement(user) {
        const userDiv = document.createElement('div');
        userDiv.classList.add('list-group-item', 'user-item');
        userDiv.setAttribute('data-user-id', user.id);
        userDiv.setAttribute('data-username', user.username);
        
        let actionButton = user.friend_request_sent ? 
            '<span class="badge bg-info">Solicitud enviada</span>' : 
            '<button class="btn btn-sm btn-outline-primary friend-action-btn" data-action="add">Agregar amigo</button>';
        
        userDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="user-info" style="cursor: pointer;">
                    <span class="user-status ${user.is_online ? 'user-online' : 'user-offline'}"></span>
                    ${user.username}
                </div>
                ${actionButton}
            </div>
        `;

        // Añadir event listeners
        const userInfo = userDiv.querySelector('.user-info');
        userInfo.addEventListener('click', () => {
            openPrivateChat(user.id, user.username);
        });

        const actionBtn = userDiv.querySelector('.friend-action-btn');
        if (actionBtn) {
            actionBtn.addEventListener('click', () => {
                friendService.sendFriendRequest(user.id);
            });
        }

        return userDiv;
    }

    // Función para manejar el cambio de tabs
    function handleTabClick(e) {
        if (e.target.matches('[data-tab]')) {
            const targetTab = e.target.getAttribute('data-tab');
            
            // Actualizar botones
            chatTabs.querySelectorAll('.btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-tab') === targetTab);
            });
            
            // Actualizar contenedores
            chatContainers.querySelectorAll('.chat-column').forEach(container => {
                container.classList.toggle('active', container.id === `${targetTab}-chat`);
            });
        }
    }

    // Event listener para los tabs
    chatTabs.addEventListener('click', handleTabClick);

    // Event listener para enviar mensaje
    sendButton.addEventListener('click', () => {
        const content = messageInput.value.trim();
        if (content) {
            webSocketService.send({
                type: 'chat_message',
                content: content,
                room: 'general'
            });
            messageInput.value = '';
        }
    });

    // Event listener para enviar mensaje con Enter
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const content = messageInput.value.trim();
            if (content) {
                webSocketService.send({
                    type: 'chat_message',
                    content: content,
                    room: 'general'
                });
                messageInput.value = '';
            }
        }
    });

    // Función para mostrar un chat privado
    function showPrivateChat(channelName, username) {
        currentPrivateChat = channelName;
        
        // Actualizar interfaz
        privateChatUsername.textContent = username;
        privateMessages.innerHTML = '';
        
        // Mostrar mensajes históricos
        const history = messageHistory.get(channelName) || [];
        history.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('msg');
            messageDiv.classList.add(msg.user_id === parseInt(localStorage.getItem('user_id')) ? 'my-msg' : 'other-msg');
            
            messageDiv.innerHTML = `
                <small class="d-block mb-1 text-muted">${msg.username}</small>
                <span>${msg.message}</span>
            `;
            privateMessages.appendChild(messageDiv);
        });
        
        privateMessages.scrollTop = privateMessages.scrollHeight;
        privateMessageInput.value = '';
        
        // Asegurarnos de que el contenedor esté visible
        const privateChatsColumn = document.getElementById('private-chats');
        privateChatsColumn.classList.add('active');
    }

    // Función para manejar los canales privados recibidos
    function handlePrivateChannels(data) {
        console.log('Canales privados recibidos:', data);
        privateChatsContainer.innerHTML = '';

        data.channels.forEach(channel => {
            const otherUser = channel.members.find(m => m.id !== parseInt(localStorage.getItem('user_id')));
            if (otherUser) {
                const chatDiv = document.createElement('div');
                chatDiv.className = 'list-group-item private-chat-item';
                chatDiv.innerHTML = `
                    <i class="fas fa-user me-2"></i>
                    ${otherUser.username}
                `;
                chatDiv.addEventListener('click', () => showPrivateChat(channel.name, otherUser.username));
                privateChatsContainer.appendChild(chatDiv);
            }
        });
    }

    // Event listener para enviar mensaje privado
    privateSendButton.addEventListener('click', () => {
        const content = privateMessageInput.value.trim();
        console.log('Intentando enviar mensaje privado:', {
            content,
            currentPrivateChat,
            active: currentPrivateChat !== null
        });
        
        if (content && currentPrivateChat) {
            webSocketService.send({
                type: 'chat_message',
                content: content,
                channel_name: currentPrivateChat
            });
            privateMessageInput.value = '';
        }
    });

    // Event listener para enviar mensaje privado con Enter
    privateMessageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const content = privateMessageInput.value.trim();
            if (content && currentPrivateChat) {
                webSocketService.send({
                    type: 'chat_message',
                    content: content,
                    channel_name: currentPrivateChat // Usar el canal directamente, sin chat_
                });
                privateMessageInput.value = '';
            }
        }
    });

    // Manejadores de eventos de amistad
    function handleFriendRequestSent(data) {
        console.log('Solicitud de amistad enviada:', data);
        
        // Guardar el estado de la solicitud enviada
        const sentRequests = JSON.parse(localStorage.getItem('sentFriendRequests') || '[]');
        sentRequests.push(data.to_user_id);
        localStorage.setItem('sentFriendRequests', JSON.stringify(sentRequests));
        
        // Actualizar la interfaz inmediatamente después de enviar la solicitud
        const userItem = document.querySelector(`.user-item[data-user-id="${data.to_user_id}"]`);
        if (userItem) {
            // Reemplazar todo el contenido de los botones
            const buttonsContainer = userItem.querySelector('.d-flex.align-items-center.gap-2');
            if (buttonsContainer) {
                buttonsContainer.innerHTML = `
                    <button class="btn btn-sm btn-primary chat-btn">
                        <i class="fas fa-comment"></i>
                    </button>
                    <span class="badge bg-info">Solicitud enviada</span>
                `;

                // Restaurar el event listener del botón de chat
                const chatBtn = buttonsContainer.querySelector('.chat-btn');
                chatBtn.addEventListener('click', () => {
                    openPrivateChat(data.to_user_id, userItem.getAttribute('data-username'));
                });
            }
        }

        // Solicitar actualización de la lista de usuarios para asegurar consistencia
        webSocketService.send({
            type: 'request_user_list'
        });
    }

    function handleFriendRequestReceived(data) {
        console.log('Solicitud de amistad recibida:', data);
        const pendingRequests = document.getElementById('pending-requests');
        
        const requestDiv = document.createElement('div');
        requestDiv.className = 'list-group-item friend-request-item';
        requestDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas fa-user me-2"></i>
                    <span>${data.from_username}</span>
                    <small class="text-muted ms-2">quiere ser tu amigo</small>
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-success accept-request" data-request-id="${data.request_id}">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn btn-sm btn-danger reject-request" data-request-id="${data.request_id}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        requestDiv.querySelector('.accept-request').addEventListener('click', () => {
            friendService.acceptFriendRequest(data.request_id);
            requestDiv.remove();
        });

        requestDiv.querySelector('.reject-request').addEventListener('click', () => {
            friendService.rejectFriendRequest(data.request_id);
            requestDiv.remove();
        });

        pendingRequests.appendChild(requestDiv);
    }

    function handleFriendRequestAccepted(data) {
        console.log('Solicitud de amistad aceptada:', data);
        
        const newFriendId = data.user_id;
        
        // Añadir al conjunto de amigos
        currentFriends.add(newFriendId);
        
        // Actualizar visualización del usuario en la lista
        const userDiv = document.querySelector(`.user-item[data-user-id="${newFriendId}"]`);
        if (userDiv) {
            userDiv.classList.add('is-friend');
        }

        // Solicitar actualizaciones
        webSocketService.send({ type: 'request_friend_list' });
    }

    function handleFriendshipDeleted(data) {
        const userId = parseInt(data.user_id);
        
        // Remover del conjunto de amigos
        currentFriends.delete(userId);
        
        // Actualizar visualización
        const userDiv = document.querySelector(`.user-item[data-user-id="${userId}"]`);
        if (userDiv) {
            userDiv.classList.remove('is-friend');
        }

        // Remover de la lista de amigos
        const friendItem = document.querySelector(`#friends-list .friend-item[data-user-id="${userId}"]`);
        if (friendItem) {
            friendItem.remove();
        }

        // Solicitar actualización de listas
        webSocketService.send({ type: 'request_user_list' });
    }

    // Añadir esta función para manejar solicitudes pendientes
    function handlePendingFriendRequests(data) {
        console.log('Solicitudes pendientes:', data);
        console.log('Estructura completa de solicitudes:', data.pending); // Debug
        const pendingRequests = document.getElementById('pending-requests');
        pendingRequests.innerHTML = ''; // Limpiar solicitudes existentes
        
        if (data.pending && Array.isArray(data.pending)) {
            data.pending.forEach(request => {
                console.log('Procesando solicitud individual:', request); // Debug
                const requestDiv = document.createElement('div');
                requestDiv.className = 'list-group-item friend-request-item';
                requestDiv.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-user me-2"></i>
                            <span>${request.from_user_username}</span>  <!-- Cambiado para usar from_user_username -->
                            <small class="text-muted ms-2">quiere ser tu amigo</small>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-success accept-request" 
                                    data-request-id="${request.request_id}">  <!-- Cambiado para usar request_id -->
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn btn-sm btn-danger reject-request" 
                                    data-request-id="${request.request_id}">  <!-- Cambiado para usar request_id -->
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                `;

                const acceptBtn = requestDiv.querySelector('.accept-request');
                acceptBtn.addEventListener('click', () => {
                    const requestId = acceptBtn.getAttribute('data-request-id');
                    console.log('Aceptando solicitud con ID:', requestId); // Debug log
                    if (requestId) {
                        webSocketService.send({
                            type: 'accept_friend_request',
                            request_id: parseInt(requestId)
                        });
                        requestDiv.remove();
                    } else {
                        console.error('No se encontró request_id en el botón');
                    }
                });

                const rejectBtn = requestDiv.querySelector('.reject-request');
                rejectBtn.addEventListener('click', () => {
                    const requestId = rejectBtn.getAttribute('data-request-id');
                    console.log('Rechazando solicitud con ID:', requestId); // Debug log
                    if (requestId) {
                        webSocketService.send({
                            type: 'reject_friend_request',
                            request_id: parseInt(requestId)
                        });
                        requestDiv.remove();
                    } else {
                        console.error('No se encontró request_id en el botón');
                    }
                });

                pendingRequests.appendChild(requestDiv);
            });
        }
    }

    // Añadir esta función para manejar la actualización de la lista de amigos
    function handleFriendListUpdate(data) {
        console.log('Lista de amigos actualizada:', data);
        const friendsList = document.getElementById('friends-list');
        friendsList.innerHTML = '';
        
        // Limpiar el conjunto de amigos antes de actualizarlo
        currentFriends.clear();

        if (data.friends && Array.isArray(data.friends)) {
            const currentUserId = parseInt(localStorage.getItem('user_id'));
            
            data.friends.forEach(friend => {
                console.log('Procesando amigo:', friend);
                
                // Determinar cuál es el otro usuario
                const isFriendUser1 = friend.user1_id === currentUserId;
                const friendId = isFriendUser1 ? friend.user2_id : friend.user1_id;
                const friendUsername = isFriendUser1 ? friend.user2__username : friend.user1__username;
                
                // Añadir al conjunto de amigos inmediatamente
                currentFriends.add(friendId);
                
                console.log('Procesando amigo:', {
                    friendId,
                    currentFriendsSize: currentFriends.size,
                    friend
                });

                const friendDiv = document.createElement('div');
                friendDiv.className = 'list-group-item friend-item';
                friendDiv.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            <span class="user-status ${friend.is_online ? 'user-online' : 'user-offline'}"></span>
                            <span class="ms-2">${isFriendUser1 ? friend.user2__username : friend.user1__username}</span>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-primary chat-with-friend" 
                                    data-user-id="${friendId}"
                                    data-username="${isFriendUser1 ? friend.user2__username : friend.user1__username}">
                                <i class="fas fa-comment"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-friend" 
                                    data-friendship-id="${friend.id}">
                                <i class="fas fa-user-minus"></i>
                            </button>
                        </div>
                    </div>
                `;

                // Añadir event listeners
                friendDiv.querySelector('.chat-with-friend').addEventListener('click', (e) => {
                    const userId = e.currentTarget.getAttribute('data-user-id');
                    const username = e.currentTarget.getAttribute('data-username');
                    openPrivateChat(parseInt(userId), username);
                });

                friendDiv.querySelector('.delete-friend').addEventListener('click', (e) => {
                    const friendshipId = e.currentTarget.getAttribute('data-friendship-id');
                    friendService.deleteFriendship(friendshipId);
                });

                friendsList.appendChild(friendDiv);
            });

            // Solo solicitar actualización de la lista de usuarios si no es la carga inicial
            if (!isInitialLoad) {
                setTimeout(() => {
                    webSocketService.send({
                        type: 'request_user_list'
                    });
                }, 100);
            }
        }
    }

    // Inicializar el chat después de crear todos los elementos del DOM
    try {
        console.log('Chat inicializado correctamente');
    } catch (error) {
        console.error('Error al inicializar el chat:', error);
    }

    // Inicializar WebSocket y añadir listeners
    await webSocketService.connect('general');  // Esperar a que se conecte

    // Añadir los listeners
    webSocketService.on('chat_message', handleHistoricalMessages);
    webSocketService.on('friend_list_update', handleFriendListUpdate);
    webSocketService.on('user_list', updateUsersList);
    webSocketService.on('private_channels', handlePrivateChannels);
    webSocketService.on('friend_request_sent', handleFriendRequestSent);
    webSocketService.on('friend_request_received', handleFriendRequestReceived);
    webSocketService.on('friend_request_accepted', handleFriendRequestAccepted);
    webSocketService.on('friendship_deleted', handleFriendshipDeleted);
    webSocketService.on('pending_friend_requests', handlePendingFriendRequests);
    webSocketService.on('error', data => {
        console.error('Error del servidor:', data.message);
        alert(data.message);
    });

    // Después de inicializar el websocket, solicitar las listas
    setTimeout(() => {
        console.log('Solicitando listas iniciales...');
        webSocketService.send({
            type: 'request_friend_list'
        });
        webSocketService.send({
            type: 'request_pending_requests'
        }); // Añadir esta línea
        setTimeout(() => {
            webSocketService.send({
                type: 'request_user_list'
            });
        }, 100);
    }, 500);

    appDiv.appendChild(container);
    return container;
}
