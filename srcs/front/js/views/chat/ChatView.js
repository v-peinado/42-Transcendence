import { webSocketService } from '../../services/WebSocketService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import AuthService from '../../services/AuthService.js';

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
        
        if (profile && profile.id) { // Cambiado de profile.user_id a profile.id
            console.log('Guardando ID de usuario:', profile.id);
            localStorage.setItem('user_id', profile.id.toString());
        } else {
            console.error('No se pudo obtener el ID de usuario del perfil:', profile);
        }
    } catch (error) {
        console.error('Error al obtener el perfil:', error);
    }

    // Verificar ID de usuario después de intentar obtenerlo
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

    let currentPrivateChat = null; // Para mantener el canal actual

    // Función para añadir mensaje al chat
    function addMessage(data) {
        const targetContainer = data.channel_name.startsWith('dm_') ? 
            privateMessages : messagesContainer;

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
    }

    // Función para actualizar lista de usuarios
    function updateUsersList(data) {
        console.log('Lista de usuarios actualizada:', {
            usuarios: data.users,
            total_usuarios: data.users.length
        });

        usersList.innerHTML = '';
        data.users.forEach(user => {
            const userDiv = document.createElement('div');
            userDiv.classList.add('list-group-item');
            userDiv.classList.add('user-item');
            userDiv.innerHTML = `
                <span class="user-status user-online"></span>
                ${user.username}
            `;
            
            // No añadir click al propio usuario
            if (user.id !== parseInt(localStorage.getItem('user_id'))) {
                userDiv.addEventListener('click', () => openPrivateChat(user.id, user.username));
            }
            
            usersList.appendChild(userDiv);
        });
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
        
        console.log('Activando chat privado:', {
            channelName,
            username,
            currentPrivateChat // verificar que se guarda correctamente
        });
        
        // Actualizar interfaz
        privateChatUsername.textContent = username;
        privateMessages.innerHTML = '';
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

    // Iniciar conexión WebSocket
    webSocketService.connect('general');
    webSocketService.on('chat_message', addMessage);
    webSocketService.on('user_list', updateUsersList);
    webSocketService.on('private_channels', handlePrivateChannels);

    appDiv.appendChild(container);

    return container;
}
