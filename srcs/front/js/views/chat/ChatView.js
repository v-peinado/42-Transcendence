import { GeneralChat } from './chatcomponents/GeneralChat.js';
import { PrivateChat } from './chatcomponents/PrivateChat.js';
import { UserList } from './chatcomponents/UserList.js';
import { FriendList } from './chatcomponents/FriendList.js';
import { ChatEventManager } from './modules/ChatEventManager.js';
import { webSocketService } from '../../services/WebSocketService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import AuthService from '../../services/AuthService.js';

export async function ChatView() {
    // Inicialización básica
    if (!await validateAuth()) return;
    
    const container = await initializeContainer();
    const eventManager = new ChatEventManager();
    
    // Inicializar componentes
    const generalChat = new GeneralChat(container);
    const privateChat = new PrivateChat(container);
    const userList = new UserList(container);
    const friendList = new FriendList(container);
    
    // Registrar manejadores de eventos
    await eventManager.initialize({
        generalChat,
        privateChat,
        userList,
        friendList
    });
    
    return container;
}

async function validateAuth() {
    if (localStorage.getItem('isAuthenticated') !== 'true') {
        window.location.href = '/login';
        return false;
    }
    
    try {
        const profile = await AuthService.getUserProfile();
        if (profile?.id) {
            localStorage.setItem('user_id', profile.id.toString());
        }
        return true;
    } catch (error) {
        console.error('Error al obtener el perfil:', error);
        return false;
    }
}

async function initializeContainer() {
    const appDiv = document.getElementById('app');
    appDiv.innerHTML = await getNavbarHTML(true, {
        username: localStorage.getItem('username')
    });

    const container = document.createElement('div');
    container.className = `chat-container ${window.location.pathname === '/chat' ? 'chat-fullscreen' : 'chat-widget'}`;
    
    const response = await fetch('/views/chat/ChatView.html');
    container.innerHTML = await response.text();
    
    appDiv.appendChild(container);
    return container;
}
