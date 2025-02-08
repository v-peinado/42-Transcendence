import { webSocketService } from '../../services/WebSocketService.js';
import { getNavbarHTML } from '../../components/Navbar.js';

export async function ChatView() {
    if (localStorage.getItem('isAuthenticated') !== 'true') {
        window.location.href = '/login';
        return;
    }

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

    // Función para añadir mensaje al chat
    function addMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('msg');
        messageDiv.classList.add(data.user_id === parseInt(localStorage.getItem('user_id')) ? 'my-msg' : 'other-msg');
        
        const username = data.username;
        const message = data.message;
        messageDiv.innerHTML = `
            <small class="d-block mb-1 text-muted">${username}</small>
            <span>${message}</span>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Función para actualizar lista de usuarios
    function updateUsersList(data) {
        usersList.innerHTML = '';
        data.users.forEach(user => {
            const userDiv = document.createElement('div');
            userDiv.classList.add('list-group-item');
            userDiv.innerHTML = `
                <span class="user-status user-online"></span>
                ${user.username}
            `;
            usersList.appendChild(userDiv);
        });
    }

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

    // Iniciar conexión WebSocket
    webSocketService.connect('general');
    webSocketService.on('chat_message', addMessage);
    webSocketService.on('user_list', updateUsersList);

    appDiv.appendChild(container);

    return container;
}
