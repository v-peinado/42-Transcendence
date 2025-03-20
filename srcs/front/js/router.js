import { LoginView } from './views/auth/LoginView.js';
import { RegisterView } from './views/auth/RegisterView.js';
import { VerifyEmailView } from './views/auth/VerifyEmailView.js';
import { VerifyEmailChangeView } from './views/auth/VerifyEmailChangeView.js';
import { UserProfileView } from './views/user/UserProfileView.js';
import { RequestPasswordResetView } from './views/auth/RequestPasswordResetView.js';
import { ResetPasswordView } from './views/auth/ResetPasswordView.js';
import { GDPRSettingsView } from './views/user/GDPRSettingsView.js';
import { NotFoundView } from './views/NotFoundView.js';
import AuthService from './services/AuthService.js';
import { getNavbarHTML } from './components/Navbar.js';
import { loadHTML, replaceContent } from './utils/htmlLoader.js';
import GameView from './views/game/GameView.js';
import { GameMatchView } from './views/game/GameMatchView.js';
import { DashboardView } from './views/dashboard/DashboardView.js';
import { LocalTournamentView } from './views/tournament/LocalTournamentView.js';
import { SinglePlayerGameView } from './views/game/SinglePlayerGameView.js';
import TournamentService from './services/TournamentService.js';
import { TournamentGameView } from './views/tournament/TournamentGameView.js';

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
    protectedRoutes = [
        '/profile',
        '/profile/',
        '/gdpr-settings',
        '/gdpr-settings/',
        '/dashboard',
        '/dashboard/',
        '/tournament',
        '/tournament/',
    ];

    checkProtectedRoute(path) {
        const normalizedPath = path.split('?')[0];
        //se excluyen las de juego, de momento
        if (normalizedPath.match(/^\/game\/\d+$/)) {
            return false;
        }
        
        const isProtected = this.protectedRoutes.some(route => normalizedPath.startsWith(route));
        if (isProtected) {
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            if (!isAuthenticated) {
                window.location.href = `/login?redirect=${path}`;
                return true;
            }
            // Verificar que el token es válido intentando obtener el perfil
            AuthService.getUserProfile().catch(() => {
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = `/login?redirect=${path}`;
                return true;
            });
        }
        return false;
    }

    routes = {
        '/': async () => {
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            if (isAuthenticated) {
                window.location.href = '/game';
                return;
            }
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
        '/game': async () => {
            try {
                const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
                if (!isAuthenticated) {
                    window.location.href = '/login?redirect=/game';
                    return;
                }
                const userInfo = await AuthService.getUserProfile();
                await GameView(userInfo);
            } catch (error) {
                console.error('Error loading game view:', error);
                window.location.href = '/login';
            }
        },
        '/game/': GameView,
        '/game/:id': async (params) => {
            try {
                // Comprobar que el usuario está autenticado
                const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
                if (!isAuthenticated) {
                    window.location.href = '/login?redirect=/game/' + params.id;
                    return;
                }

                // Verificar que el ID es un número
                const gameId = parseInt(params.id);
                if (isNaN(gameId)) {
                    await this.routes['/404']();
                    return;
                }

                // Cargar la vista de juego
                await GameMatchView(params.id);
            } catch (error) {
                console.error('Error cargando partida:', error);
                await this.routes['/404']();
            }
        },
        '/dashboard': DashboardView,
        '/dashboard/': DashboardView,
        '/tournament/local': LocalTournamentView,
        '/tournament/local/': LocalTournamentView,
        // Primera ruta específica para el torneo
        '/tournament/game/:tournamentId/:matchId': (params) => {
            console.log('Cargando partida específica:', params);
            return TournamentGameView(params.tournamentId, params.matchId);
        },
        // Luego la ruta general del torneo
        '/tournament/game/:tournamentId': async (params) => {
            console.log('Iniciando torneo:', params.tournamentId);
            try {
                // Primero iniciar el torneo
                await TournamentService.startTournament(params.tournamentId);
                // Obtener detalles después de iniciarlo
                const tournament = await TournamentService.getTournamentDetails(params.tournamentId);
                console.log('Detalles del torneo:', tournament);
                
                if (tournament.pending_matches && tournament.pending_matches.length > 0) {
                    const match = tournament.pending_matches[0];
                    console.log('Redirigiendo a primera partida:', match.id);
                    window.location.href = `/tournament/game/${params.tournamentId}/${match.id}`;
                } else {
                    console.error('No hay partidas pendientes');
                    window.location.href = '/tournament/local';
                }
            } catch (error) {
                console.error('Error al iniciar torneo:', error);
                window.location.href = '/tournament/local';
            }
        },
        '/game/single-player': SinglePlayerGameView,
        '/game/single-player/': SinglePlayerGameView,
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

        // Verificar rutas protegidas primero
        if (this.checkProtectedRoute(path)) {
            return;
        }

        // Si estamos en la página principal, verificar autenticación primero
        if (path === '/' || path === '') {
            const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
            if (isAuthenticated) {
                window.location.href = '/game';
                return;
            }
            await this.renderHomePage(false);
            return;
        }

        // Manejar rutas de juego específicamente 
        if (path.startsWith('/game/')) {
            const gameMatch = path.match(/^\/game\/(\d+)$/);
            if (gameMatch) {
                const gameId = gameMatch[1];

                // Verificar que es un número válido
                if (!isNaN(parseInt(gameId))) {
                    console.log('Cargando partida:', gameId);
                    try {
                        // Verificar autenticación primero
                        if (localStorage.getItem('isAuthenticated') !== 'true') {
                            window.location.href = '/login?redirect=' + path;
                            return;
                        }

                        // Verificar si hay datos de sesión guardados (para reconexión)
                        const savedData = localStorage.getItem(`game_${gameId}`);
                        if (savedData) {
                            console.log('Datos de reconexión encontrados para partida', {
                                gameId,
                                data: JSON.parse(savedData)
                            });
                        }

                        // Intentar cargar la vista incluso si hay error de API
                        await GameMatchView(gameId);
                        return;
                    } catch (error) {
                        console.error('Error cargando partida inicial:', error);
                        // Continuar al manejo normal de rutas que mostrará 404
                    }
                }
            }
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

        // Verificar rutas protegidas primero
        if (this.checkProtectedRoute(path)) {
            return;
        }

        // Reset data-page attribute
        document.body.removeAttribute('data-page');

        // Manejar rutas de juego específicamente
        if (path.startsWith('/game/')) {
            const gameMatch = path.match(/^\/game\/(\d+)$/);
            if (gameMatch) {
                const gameId = gameMatch[1];

                // Verificar que es un número válido
                if (!isNaN(parseInt(gameId))) {
                    console.log('Cargando partida:', gameId);
                    try {
                        // Verificar autenticación primero
                        if (localStorage.getItem('isAuthenticated') !== 'true') {
                            window.location.href = '/login?redirect=' + path;
                            return;
                        }

                        // Verificar si hay datos de sesión guardados (para reconexión)
                        const savedData = localStorage.getItem(`game_${gameId}`);
                        if (savedData) {
                            console.log('Datos de reconexión encontrados para partida', {
                                gameId,
                                data: JSON.parse(savedData)
                            });
                        }

                        // Intentar cargar la vista incluso si hay error de API
                        await GameMatchView(gameId);
                        return;
                    } catch (error) {
                        console.error('Error cargando partida', error);
                        // Continuar al manejo normal de rutas que mostrará 404
                    }
                }
            }
        }

        // Manejar rutas de torneo específicamente
        if (path.startsWith('/tournament/game/')) {
            const matches = path.match(/^\/tournament\/game\/(\d+)(?:\/(\d+))?$/);
            if (matches) {
                const [, tournamentId, matchId] = matches;
                if (matchId) {
                    // Ruta para partido específico
                    await TournamentGameView(tournamentId, matchId);
                } else {
                    try {
                        // Iniciar torneo y redirigir al primer partido
                        await TournamentService.startTournament(tournamentId);
                        const tournament = await TournamentService.getTournamentDetails(tournamentId);
                        if (tournament.pending_matches && tournament.pending_matches.length > 0) {
                            window.location.href = `/tournament/game/${tournamentId}/${tournament.pending_matches[0].id}`;
                        } else {
                            window.location.href = '/tournament/local';
                        }
                    } catch (error) {
                        console.error('Error al iniciar torneo:', error);
                        window.location.href = '/tournament/local';
                    }
                }
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
