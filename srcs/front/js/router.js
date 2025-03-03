import { LoginView } from '/js/views/auth/LoginView.js';
import { RegisterView } from '/js/views/auth/RegisterView.js';
import { VerifyEmailView } from '/js/views/auth/VerifyEmailView.js';
import { VerifyEmailChangeView } from '/js/views/auth/VerifyEmailChangeView.js';
import { UserProfileView } from '/js/views/user/UserProfileView.js';
import { RequestPasswordResetView } from '/js/views/auth/RequestPasswordResetView.js';
import { ResetPasswordView } from '/js/views/auth/ResetPasswordView.js';
import { GDPRSettingsView } from '/js/views/user/GDPRSettingsView.js';
import { NotFoundView } from '/js/views/NotFoundView.js';
import AuthService from '/js/services/AuthService.js';
import { getNavbarHTML } from '/js/components/Navbar.js';
import { loadHTML, replaceContent } from '/js/utils/htmlLoader.js';
import GameView from './views/game/GameView.js';
import { GameMatchView } from '/js/views/game/GameMatchView.js';

class Router {
    constructor() {
        // Solo limpiar sesión si NO estamos autenticados
        const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
        
        if (!isAuthenticated && (
            window.location.pathname === '/' || 
            window.location.pathname === '/login'
        )) {
            AuthService.clearSession().then(() => {
                setTimeout(() => {
                    this.handleInitialRoute();
                }, 100);
            });
            return;
        }
        
        this.handleInitialRoute();
        
        // Añadir manejo de navegación
        window.addEventListener('popstate', () => this.handleRoute());
        document.addEventListener('click', e => {
            if (e.target.matches('[data-link]')) {
                e.preventDefault();
                this.navigateTo(e.target.href);
            }
        });

        // Añadir event listener global para logout
        document.addEventListener('click', async (e) => {
            if (e.target && (e.target.classList.contains('logout-btn') || e.target.closest('.logout-btn'))) {
                e.preventDefault();
                try {
                    await AuthService.logout();
                    localStorage.clear();
                    sessionStorage.clear();
                    window.location.replace('/');
                } catch (error) {
                    console.error('Error en logout:', error);
                    // Intentar cerrar sesión de todas formas
                    localStorage.clear();
                    sessionStorage.clear();
                    window.location.replace('/');
                }
            }
        });
    }

    routes = {
        '/': async () => {
            const app = document.getElementById('app');
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            
            if (isAuthenticated) {
                try {
                    const userInfo = await AuthService.getUserProfile();
                    if (userInfo && !userInfo.error) {
                        await this.renderHomePage(true, userInfo);
                        return;
                    }
                } catch (error) {
                    console.error('Error loading profile:', error);
                }
                // Si hay error, limpiar estado
                localStorage.clear();
                sessionStorage.clear();
            }
            // Si no está autenticado o hubo error, mostrar página no autenticada
            await this.renderHomePage(false);
        },
        '/login': LoginView,
        '/register': RegisterView,
        '/verify-email/:uid/:token': VerifyEmailView,
        '/verify-email-change/:uid/:token': VerifyEmailChangeView,
        '/verify-email-change/:uid/:token/': VerifyEmailChangeView,
        '/profile': UserProfileView,
        '/profile/': UserProfileView,
        '/reset_password': RequestPasswordResetView,
        '/reset/:uid/:token': ResetPasswordView,
        '/gdpr-settings': GDPRSettingsView,
        '/gdpr-settings/': GDPRSettingsView,
        '/game': GameView,
        '/game/': GameView,
        '/game/:id': GameMatchView,  // Definición de ruta con parámetro
        '/404': NotFoundView,
    };

    async renderHomePage(isAuthenticated, userInfo = null) {
        const app = document.getElementById('app');
        app.textContent = '';
        
        const [pageHtml, navbarHtml, footerHtml] = await Promise.all([
            loadHTML(isAuthenticated ? '/views/home/AuthenticatedHome.html' : '/views/home/HomePage.html'),
            loadHTML(isAuthenticated ? '/views/components/NavbarAuthenticated.html' : '/views/components/NavbarUnauthorized.html'),
            loadHTML('/views/components/Footer.html')
        ]);
        
        const parser = new DOMParser();
        const navDoc = parser.parseFromString(navbarHtml, 'text/html');
        const mainDoc = parser.parseFromString(pageHtml, 'text/html');
        const footerDoc = parser.parseFromString(footerHtml, 'text/html');
        
        // Actualizar información del usuario si es necesario
        if (isAuthenticated && userInfo) {
            const navElement = navDoc.body.firstElementChild;
            const mainElement = mainDoc.body.firstElementChild;
            
            const profileImage = userInfo?.profile_image || 
                               userInfo?.fortytwo_image || 
                               `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;

            navElement.querySelectorAll('#nav-profile-image, #nav-profile-image-large').forEach(img => {
                img.src = profileImage;
                img.onerror = () => img.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;
            });

            navElement.querySelectorAll('#nav-username, #nav-username-large').forEach(el => {
                el.textContent = userInfo.username;
            });
            
            const usernameElement = mainElement.querySelector('#username-placeholder');
            if (usernameElement) {
                usernameElement.textContent = userInfo.username;
            }
        }
        
        // Renderizar todo en orden
        app.appendChild(navDoc.body.firstElementChild);
        app.appendChild(mainDoc.body.firstElementChild);
        app.appendChild(footerDoc.body.firstElementChild);
    }

    async handleLogout() {
        try {
            await AuthService.logout();
            // Desconectar WebSocket antes de limpiar
            webSocketService.disconnect();
            // Limpiar todo
            localStorage.clear();
            sessionStorage.clear();
            // Limpiar cookies
            document.cookie.split(';').forEach(cookie => {
                const name = cookie.split('=')[0].trim();
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;`;
            });
            window.location.href = '/';
        } catch (error) {
            console.error('Error en logout:', error);
        }
    }

    async handleInitialRoute() {
        const path = window.location.pathname + window.location.search;
        console.log('Ruta inicial completa:', path);  // Debug

        // Si estamos en la página principal, verificar autenticación primero
        if (path === '/' || path === '') {
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            if (isAuthenticated) {
                try {
                    const userInfo = await AuthService.getUserProfile();
                    if (userInfo && !userInfo.error) {
                        await this.renderHomePage(true, userInfo);
                        return;
                    }
                } catch (error) {
                    console.error('Error loading profile:', error);
                }
            }
            // Si no está autenticado o hay error, mostrar página normal
            await this.renderHomePage(false);
            return;
        }

        // Manejar código de 42 primero
        const searchParams = new URLSearchParams(window.location.search);
        const code = searchParams.get('code');

        if (path.startsWith('/login') && code) {
            // Render inmediato de LoginView
            LoginView();
            return;
        }

        // Manejar verificación de email
        if (path.includes('/verify-email/')) {
            const parts = path.split('/verify-email/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1].replace('/', '');
                console.log('Verificando email (inicial):', { uidb64, token });
                VerifyEmailView(uidb64, token);
                return;
            }
        }

        // Verificar cambio de email
        if (path.includes('/verify-email-change/')) {
            const parts = path.split('/verify-email-change/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1].replace('/', '');
                console.log('Verificando cambio de email:', { uidb64, token });
                VerifyEmailChangeView(uidb64, token);
                return;
            }
        }

        // Añadir manejo de reset de contraseña
        if (path.includes('/reset/')) {
            const parts = path.split('/reset/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1];
                ResetPasswordView(uidb64, token);
                return;
            }
        }

        const normalizedPath = path.split('?')[0];
        const route = this.routes[normalizedPath] || this.routes['/404'];
        
        if (typeof route === 'function') {
            if (route.constructor.name === 'AsyncFunction') {
                route().catch(console.error);  // Manejar promesas rechazadas
            } else {
                route();
            }
        }
    }

    async handleRoute() {
        const path = window.location.pathname + window.location.search;
        console.log('Manejando ruta completa:', path);

        // Reset data-page attribute
        document.body.removeAttribute('data-page');

        // Manejar rutas de juego específicamente
        if (path.startsWith('/game/')) {
            const gameMatch = path.match(/^\/game\/(\d+)$/);
            if (gameMatch) {
                const gameId = gameMatch[1];
                console.log('Cargando partida:', gameId);
                await GameMatchView(gameId);
                return;
            }
        }

        // Manejar login con código de 42
        if (path.startsWith('/login') && path.includes('code=')) {
            await LoginView();
            return;
        }

        // Manejar verificación de email
        if (path.includes('/verify-email/')) {
            const parts = path.split('/verify-email/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1].replace('/', '');
                console.log('Verificando email:', { uidb64, token });
                VerifyEmailView(uidb64, token);
                return;
            }
        }

        // Verificar cambio de email
        if (path.includes('/verify-email-change/')) {
            const parts = path.split('/verify-email-change/')[1].split('/');
            if (parts.length >= 2) {
                const uidb64 = parts[0];
                const token = parts[1];
                console.log('Verificando cambio de email:', { uidb64, token });
                VerifyEmailChangeView(uidb64, token);
                return;
            }
        }

        // Verificar rutas protegidas
        if ((path.startsWith('/profile') || path.startsWith('/game')) && 
            localStorage.getItem('isAuthenticated') !== 'true') {
            window.location.href = '/login';
            return;
        }

        const normalizedPath = path.split('?')[0];
        const route = this.routes[normalizedPath] || this.routes['/404'];
        
        if (typeof route === 'function') {
            try {
                await route();
            } catch (error) {
                console.error('Error al cargar la ruta:', error);
                this.routes['/404']();
            }
        }
    }

    navigateTo(url) {
        // Si es la página principal y el usuario está autenticado, forzar recarga
        if (url === '/' && localStorage.getItem('isAuthenticated') === 'true') {
            window.location.reload();
            return;
        }
        window.history.pushState(null, null, url);
        this.handleRoute();
    }
}


export default Router;
